"""MCP authentication + authorisation (roadmap B-205, Phase 19).

Two roads in, one law once inside:

* **Local (stdio): an agent-seat API key.** The seat's own key
  from B-014/B-018 — hashed at rest, shown once at issue,
  revocable — presented through the ``GPA_MCP_SEAT_API_KEY``
  setting by the process that spawns the server. The key
  resolves to exactly one seat in exactly one group, with that
  seat's role and the key's scopes. Nothing else about the
  spawning process is trusted: a key that does not resolve, or
  resolves to a person's key rather than a seat's, is refused.
* **Remote (streamable HTTP): OAuth 2.1 resource-server
  profile.** This server is a *resource server* in the sense of
  the current MCP authorisation specification: it does not
  issue tokens and runs no consent flow; it VERIFIES bearer
  tokens an authorisation server issued for it. A token must
  carry an audience (``aud``) naming this server's resource
  URL, an expiry (``exp``) in the future, a subject (``sub``),
  and scopes — and its HS256 signature must verify against the
  deployment's verification secret (``GPA_MCP_OAUTH_SECRET``,
  falling back to the app secret in the development posture,
  the same documented posture as B-163/B-164's derived keys).

Scopes, and the mapping onto internal scopes:

* The credential scopes are the product's own ladder from
  B-014 — ``read`` / ``draft`` / ``publish`` / ``admin``.
* Each MCP tool names the ONE credential scope it requires in
  :data:`TOOL_SCOPES`. A call re-checks that scope **at call
  time, not at connect time**: the server resolves its
  principal fresh for every tool call (the seat-key road
  re-reads the key row, so revocation lands on the next call;
  the OAuth road re-reads the request's verified token), so a
  credential weakened or revoked after connecting loses its
  powers immediately, not at the next handshake.
* :data:`EXTERNAL_TO_INTERNAL` states, in one auditable table,
  how a credential scope maps onto the internal API's scopes
  (B-162) — the layer beneath this one. The bridge's gateway
  grants (B-204) carry the call; THIS table is what a given
  principal may ask the gateway to carry for them.

The MCP-correct errors: authentication failures raise the
backend's own registry codes — ``token_expired`` for an
expired token, ``token_invalid`` for a malformed, badly
signed, or wrong-audience token, ``not_authenticated`` for a
seat key that does not resolve — and an authenticated but
under-scoped call raises ``insufficient_scope``. Over the HTTP
transport the SDK's bearer middleware turns a verifier refusal
into the specification's 401 (with the resource-metadata
challenge); inside a session, an under-scoped TOOL call
travels as a tool error leading with ``insufficient_scope``,
exactly like every other backend refusal (B-204's rule).

This module imports no service, router, or model (the B-204
boundary): the seat-key lookup is a parameterised SQL read of
the credential tables through the bridge's own session — the
chassis door, never a domain import — and token verification
is hand-rolled HS256 over the standard library, following the
house pattern of ``gpa.security`` without importing a domain
layer. :func:`issue_oauth_token` exists so tests (and a
development authorisation-server stand-in) can mint the tokens
this verifier accepts; production tokens are an external
authorisation server's to issue, and this function is never
called by the serving path.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass

from sqlalchemy import text

from gpa.config import Settings
from gpa.errors import AppError
from gpa.security import hash_secret

# The credential scope ladder (B-014), least first. A token or
# key naming anything outside this set is carrying words this
# product never granted — refused as invalid, never ignored.
KNOWN_SCOPES = ("read", "draft", "publish", "admin")

# The internal API's scopes (B-162 registry), for the mapping
# table below: the complete set an ``admin`` credential maps to.
INTERNAL_SCOPES = (
    "candidates:write",
    "events:publish",
    "notify:write",
    "jobs:write",
    "ai:submit",
    "integrations:write",
)

# Credential scope -> the internal scopes it maps onto. This is
# the "mapped onto internal scopes" sentence of B-205 made into
# one table a reviewer can read whole: reading maps to no
# internal write at all (the read tools travel operations whose
# scope the gateway already holds), drafting maps to the queue,
# publishing adds the publish door, and admin maps to the full
# internal set — mirroring how a person's session (scopes=None
# in deps.py) carries every scope.
EXTERNAL_TO_INTERNAL: dict[str, frozenset[str]] = {
    "read": frozenset(),
    "draft": frozenset({"candidates:write"}),
    "publish": frozenset({"candidates:write", "events:publish"}),
    "admin": frozenset(INTERNAL_SCOPES),
}

# Tool -> the credential scope a call to it requires. Every
# tool the server registers must appear here (a test asserts
# the sets agree), so a new tool cannot quietly ship without a
# stated scope — B-206's generated registry inherits this table.
TOOL_SCOPES: dict[str, str] = {
    "gpa_server_info": "read",
    "gpa_list_internal_operations": "read",
    "gpa_create_candidate_draft": "draft",
    "gpa_publish_event": "publish",
}


@dataclass(frozen=True)
class McpPrincipal:
    """Who an MCP call speaks for, resolved fresh per call.

    ``kind`` is ``seat`` (a seat-key or a seat-subject token),
    ``user`` (a person-subject token), or ``local`` (the stdio
    road with no seat key configured: the spawning process's
    own trusted operator, carrying every scope — B-204's stated
    posture, named here rather than left implicit). ``scopes``
    is the credential's scope set; the local principal carries
    the full ladder, exactly as a person's session does.
    """

    # Which of the three kinds above this principal is.
    kind: str
    # The seat this principal acts as, when kind == "seat".
    seat_id: str | None = None
    # The seat's one group, when kind == "seat".
    group_id: str | None = None
    # The seat's role on the group's ladder, when a seat.
    role: str | None = None
    # A person's user id, when kind == "user".
    user_id: str | None = None
    # The credential's scopes (subset of KNOWN_SCOPES).
    scopes: frozenset[str] = frozenset()
    # The credential row's id (seat keys), for audit correlation.
    key_id: str | None = None
    # The token's subject / client, for the OAuth road.
    subject: str = ""
    # How this principal authenticated: seat_key | oauth | local.
    auth_method: str = "local"

    @property
    def label(self) -> str:
        """The audit label: a seat's work is the seat's (B-018)."""
        # Mirrors deps.Principal.label exactly — the same words
        # in every audit line, whichever door the work came in.
        if self.kind == "seat":
            return f"seat:{self.seat_id}"
        if self.kind == "user":
            return f"user:{self.user_id}"
        return "local:stdio"

    def internal_scopes(self) -> frozenset[str]:
        """This principal's scopes mapped onto internal scopes."""
        # The union over the mapping table: holding two
        # credential scopes means holding both mappings.
        mapped: set[str] = set()
        for scope in self.scopes:
            mapped |= EXTERNAL_TO_INTERNAL.get(scope, frozenset())
        return frozenset(mapped)


# The principal a keyless local stdio process acts as. Frozen
# and shared: it carries no group content and grants nothing
# beyond what the spawning operator could do at their own
# terminal — the road B-204 documented and B-205 names.
LOCAL_PRINCIPAL = McpPrincipal(
    kind="local",
    scopes=frozenset(KNOWN_SCOPES),
    auth_method="local",
)


# The scope check is deliberately a pure function of
# (principal, tool): no I/O, no caching, no clock — so the
# call-time re-check costs nothing to run on every call and
# can be unit-tested as a table. The server's guard calls it
# fresh for each tool invocation; nothing in this module ever
# memoises a principal's scopes across calls, because a
# memoised answer is precisely the connect-time fact B-205
# forbids the authorisation to rest on.
def require_tool_scope(principal: McpPrincipal, tool: str) -> str:
    """Check, at call time, that ``principal`` may call ``tool``.

    Returns the scope the tool required (for the call's log
    line). Raises ``insufficient_scope`` — the registry's 403 —
    when the credential does not carry it, and
    ``internal_unknown_operation``-style honesty is preserved
    for an unregistered tool name via ``validation_error``: a
    tool with no stated scope is a build bug, never a free pass.
    """
    required = TOOL_SCOPES.get(tool)
    if required is None:
        # No scope on record for this tool name: refuse rather
        # than guess — the registry test keeps this unreachable.
        raise AppError(
            "validation_error",
            detail=f"No scope is registered for the MCP tool '{tool}'.",
        )
    if required not in principal.scopes and "admin" not in principal.scopes:
        # Admin carries every lesser scope, as it does on the
        # HTTP API (a session/key with admin is the top rung).
        raise AppError(
            "insufficient_scope",
            detail=f"This tool needs the '{required}' scope.",
        )
    return required


# A note on what this module does NOT do, for the reviewer:
# it never issues a seat key (B-014's doors do that, through
# the API, by a person), it never decides a seat's ROLE (the
# seat row does, set by the group's admins), and it never
# widens a scope (the mapping table only ever translates the
# scopes a credential already carries). Authentication here
# is a reading of facts decided elsewhere — which is exactly
# why it can sit at the boundary without becoming a second
# source of permission truth in the system.

# --- The local road: agent-seat API keys ------------------------------------


# The seat-key lookup reads two columns of law from the seat
# row (its group and its role) alongside the key's own scopes:
# the principal that comes out must be able to answer "which
# seat, in which group, at which role, holding which scopes"
# without a second query, because tool handlers downstream
# (B-207 onward) will ask exactly those questions of it.
def authenticate_seat_key(session, raw_key: str) -> McpPrincipal:
    """Resolve a seat API key to its principal, or refuse.

    One parameterised SQL read joining the key row to its seat:
    the key must exist by hash, be unrevoked, and belong to a
    SEAT (a person's key is a different credential for a
    different door — presenting one here is ``not_authenticated``,
    never a silent upgrade). On success the key's last-used
    stamp moves, in the caller's transaction.
    """
    if not raw_key:
        # An empty configured key is "no key configured", and the
        # caller decides what that means; reaching here with one
        # is a refusal, not a local principal.
        raise AppError("not_authenticated", detail="No seat API key was presented.")
    row = session.execute(
        text(
            "SELECT k.id AS key_id, k.scopes AS scopes, "
            "s.id AS seat_id, s.group_id AS group_id, s.role AS role "
            "FROM api_keys k JOIN agent_seats s ON s.id = k.seat_id "
            "WHERE k.key_hash = :hash AND k.revoked_at IS NULL"
        ),
        {"hash": hash_secret(raw_key)},
    ).mappings().one_or_none()
    if row is None:
        raise AppError("not_authenticated", detail="That seat API key is not valid.")
    session.execute(
        text("UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": row["key_id"]},
    )
    scopes = frozenset(s for s in row["scopes"].split(",") if s in KNOWN_SCOPES)
    return McpPrincipal(
        kind="seat",
        seat_id=row["seat_id"],
        group_id=row["group_id"],
        role=row["role"],
        scopes=scopes,
        key_id=row["key_id"],
        subject=f"seat:{row['seat_id']}",
        auth_method="seat_key",
    )


def seat_key_provider(bridge, raw_key: str):
    """A per-call principal provider over the seat-key road.

    The returned callable re-authenticates on EVERY call — a
    fresh session, a fresh key-row read, a commit of the
    last-used stamp — so a key revoked (or re-scoped) after the
    server started loses its powers on the very next tool call.
    That is the call-time re-check B-205 requires, implemented
    as re-resolution rather than as a cached connect-time fact.
    """

    def _provide() -> McpPrincipal:
        """Re-resolve the configured seat key, right now."""
        session = bridge.new_session()
        try:
            principal = authenticate_seat_key(session, raw_key)
            session.commit()
            return principal
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return _provide


# --- The remote road: OAuth 2.1 resource-server verification -----------------


def resource_url(settings: Settings) -> str:
    """This server's resource URL — the audience tokens name.

    An explicit ``GPA_MCP_RESOURCE_URL`` wins; otherwise the URL
    is derived from the HTTP transport's bind address, so a
    deployment that moves the port moves its audience with it
    and old tokens fail the audience check, as they should.
    """
    if settings.mcp_resource_url:
        return settings.mcp_resource_url
    return f"http://{settings.mcp_http_host}:{settings.mcp_http_port}/mcp"


def issuer_url(settings: Settings) -> str:
    """The authorisation server's URL, for the auth metadata.

    ``GPA_MCP_OAUTH_ISSUER_URL`` names the external AS; the
    development fallback is this server's own origin, which is
    where a development stand-in AS would be mounted.
    """
    if settings.mcp_oauth_issuer_url:
        return settings.mcp_oauth_issuer_url
    return f"http://{settings.mcp_http_host}:{settings.mcp_http_port}"


def _verification_secret(settings: Settings) -> str:
    """The HS256 verification secret for OAuth bearer tokens.

    The dedicated ``GPA_MCP_OAUTH_SECRET`` when set; otherwise
    the app secret — the development posture this codebase uses
    for every derived key (B-163/B-164), stated here in the open.
    """
    return settings.mcp_oauth_secret or settings.secret_key


def _b64url_encode(raw: bytes) -> str:
    """base64url without padding, as JWT requires (RFC 7519)."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text_value: str) -> bytes:
    """Inverse of :func:`_b64url_encode` (restores padding)."""
    return base64.urlsafe_b64decode(text_value + "=" * (-len(text_value) % 4))


def issue_oauth_token(
    settings: Settings,
    *,
    subject: str,
    scopes: list[str],
    audience: str | None = None,
    minutes: int = 15,
    client_id: str = "mcp-client",
    seat_id: str | None = None,
    group_id: str | None = None,
    role: str | None = None,
) -> str:
    """Mint an HS256 bearer token this verifier accepts.

    A development/test issuer stand-in ONLY: production tokens
    are an external authorisation server's to issue (this server
    is the resource server, never the AS). Claims follow the
    MCP authorisation profile: ``sub``, ``aud``, ``exp``,
    ``iat``, ``jti``, ``client_id``, and ``scope`` as the
    spec's space-joined string; seat facts ride as claims so a
    seat-subject token resolves to the same principal shape as
    the seat-key road.
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, object] = {
        "sub": subject,
        "aud": audience if audience is not None else resource_url(settings),
        "exp": now + minutes * 60,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "client_id": client_id,
        "scope": " ".join(scopes),
    }
    if seat_id is not None:
        payload["seat_id"] = seat_id
    if group_id is not None:
        payload["group_id"] = group_id
    if role is not None:
        payload["role"] = role
    signing_input = (
        f"{_b64url_encode(json.dumps(header).encode())}"
        f".{_b64url_encode(json.dumps(payload).encode())}"
    )
    signature = hmac.new(
        _verification_secret(settings).encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


# Verification is pure: settings + token in, principal or
# AppError out, no database touched. That purity is what lets
# the SDK middleware call it per request without a session,
# and what keeps the three acceptance failures (expired,
# wrong audience, under-scoped) testable as plain function
# calls — under-scoped is checked one layer up, in
# require_tool_scope, because scope is per-tool, not per-token.
def verify_oauth_token(settings: Settings, token: str) -> McpPrincipal:
    """Verify one bearer token and resolve its principal.

    The checking order is the specification's: structure and
    signature first (``token_invalid``), then expiry
    (``token_expired`` — told apart because the fix differs),
    then audience (``token_invalid``, naming the mismatch),
    then the scope vocabulary. A token that passes all four is
    a principal; anything else never becomes one.
    """
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(
            _verification_secret(settings).encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _b64url_decode(signature_b64)):
            raise AppError("token_invalid")
        payload = json.loads(_b64url_decode(payload_b64))
    except AppError:
        raise
    except Exception:
        # Any structural failure — wrong segment count, bad
        # base64, unparseable claims — is one answer: invalid.
        raise AppError("token_invalid") from None
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AppError("token_expired")
    expected_audience = resource_url(settings)
    if payload.get("aud") != expected_audience:
        raise AppError(
            "token_invalid",
            detail="That token was issued for a different resource.",
        )
    raw_scope = payload.get("scope", "")
    claimed = raw_scope.split() if isinstance(raw_scope, str) else list(raw_scope)
    if any(scope not in KNOWN_SCOPES for scope in claimed):
        raise AppError("token_invalid", detail="That token names an unknown scope.")
    subject = str(payload.get("sub") or "")
    seat_id = payload.get("seat_id") or (
        subject.removeprefix("seat:") if subject.startswith("seat:") else None
    )
    if seat_id:
        return McpPrincipal(
            kind="seat",
            seat_id=str(seat_id),
            group_id=payload.get("group_id"),
            role=payload.get("role"),
            scopes=frozenset(claimed),
            subject=subject,
            auth_method="oauth",
        )
    return McpPrincipal(
        kind="user",
        user_id=subject.removeprefix("user:") if subject.startswith("user:") else subject,
        scopes=frozenset(claimed),
        subject=subject,
        auth_method="oauth",
    )


def principal_from_access_token(access_token) -> McpPrincipal:
    """Resolve the SDK's verified access token to a principal.

    The HTTP transport's middleware has already verified the
    token (signature, expiry, audience) before a tool runs;
    this maps its claims onto the same principal shape the
    other roads produce, so the call-time scope check that
    follows is one code path for every road.
    """
    claims = dict(access_token.claims or {})
    subject = access_token.subject or claims.get("sub", "") or ""
    seat_id = claims.get("seat_id") or (
        subject.removeprefix("seat:") if subject.startswith("seat:") else None
    )
    scopes = frozenset(s for s in access_token.scopes if s in KNOWN_SCOPES)
    if seat_id:
        return McpPrincipal(
            kind="seat",
            seat_id=str(seat_id),
            group_id=claims.get("group_id"),
            role=claims.get("role"),
            scopes=scopes,
            subject=subject,
            auth_method="oauth",
        )
    return McpPrincipal(
        kind="user",
        user_id=subject.removeprefix("user:") if subject.startswith("user:") else subject,
        scopes=scopes,
        subject=subject,
        auth_method="oauth",
    )


class OAuthTokenVerifier:
    """The SDK ``TokenVerifier`` seam over :func:`verify_oauth_token`.

    The SDK's bearer middleware asks this class, per request,
    whether a token is good; a refusal returns None and the
    middleware answers the specification's 401 challenge. The
    precise reason (expired vs wrong audience) is preserved on
    :meth:`verify_oauth_token`'s AppError for direct callers and
    tests — the wire answer is deliberately the coarser one,
    as the specification intends.
    """

    def __init__(self, settings: Settings) -> None:
        """Bind the verifier to one deployment's settings."""
        self._settings = settings

    async def verify_token(self, token: str):
        """Verify ``token``; return the SDK AccessToken or None."""
        # Imported here: the SDK types are this seam's own
        # vocabulary, paid only by processes that serve HTTP.
        from mcp.server.auth.provider import AccessToken

        try:
            principal = verify_oauth_token(self._settings, token)
        except AppError:
            return None
        # Re-read the claims for the AccessToken's fields — the
        # token verified, so this parse cannot fail in practice;
        # the guard keeps a surprise a refusal, never a crash.
        try:
            payload = json.loads(_b64url_decode(token.split(".")[1]))
        except Exception:
            return None
        return AccessToken(
            token=token,
            client_id=str(payload.get("client_id") or "mcp-client"),
            scopes=sorted(principal.scopes),
            expires_at=int(payload["exp"]),
            resource=str(payload.get("aud")),
            subject=principal.subject,
            claims=payload,
        )
