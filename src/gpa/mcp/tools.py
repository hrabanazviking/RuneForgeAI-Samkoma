"""The MCP tool registry — one source of truth (roadmap B-206).

What this module is, and the law it makes mechanical:

* **Generated, not hand-listed.** The MCP tool catalogue is
  GENERATED from the internal operation registry (B-162) plus
  the curated annotation layer in this file. An operation that
  is registered on the internal API has exactly one MCP tool;
  an MCP operation tool names exactly one registered operation.
  The two directions are both checked — by
  :func:`check_tool_registry` here and by the B-201 parity
  checker, which now runs this check as its MCP leg — so a
  capability cannot exist on one surface and be missing from
  the other without a test failing BY NAME.
* **The curated layer is annotation, never capability.** The
  annotation table below gives each operation its tool name,
  its served description, and the credential scope a call to it
  requires. It cannot create a capability: an annotation naming
  no registered operation is a checker failure, and an operation
  with no annotation is a checker failure too — the fix in both
  cases is a deliberate act in this file, visible in review.
* **Meta tools are declared, not smuggled.** Two tools are not
  operation-backed: ``gpa_server_info`` and
  ``gpa_list_internal_operations`` report on the server itself
  and carry no group content. They are registered here with
  ``kind="meta"`` and ``operation=None`` so the checker can tell
  a declared meta tool from an unregistered capability.
* **Descriptions are release facts (tool-poisoning defence).**
  The description an agent reads is part of how it decides to
  call a tool; a swapped description is a swapped instruction.
  :func:`tool_manifest` therefore emits every tool's name,
  operation, scope, and description together with a SHA-256 of
  the description and one digest over the whole manifest, and
  the release builder (scripts/make_release_zip.py) stamps both
  into the SIGNED release manifest — a release whose served
  descriptions differ from its manifest's is a tampered
  release, detectable by anyone holding the manifest.
* **Scope law.** An operation tool's credential scope must map,
  through B-205's ``EXTERNAL_TO_INTERNAL`` table, onto the
  operation's required internal scope. The checker enforces it,
  so a tool can never be callable by a credential whose mapped
  internal scopes could not carry its operation.

This module imports the internal registry and (lazily, inside
the checker) the handlers that fill it — the same door the rest
of the MCP package uses. It imports no service, router, or
model directly, and it builds no server: ``gpa.mcp.server``
consumes these specs, it does not restate them.

How generation walks, step by step
----------------------------------
1. ``handlers.register_all()`` fills the internal registry —
   registration is lazy in the internal API by design (the
   client's first call does it), and a generator that read the
   registry cold would generate from an empty table and call
   the result a catalogue.
2. For each registered operation, in name order, the curated
   annotation layer is consulted. A hit becomes a ToolSpec
   verbatim: the annotation's tool name, scope, and description
   are the spec's, because those words ARE the release facts.
3. A miss raises, naming the operation. There is no default
   description and no default scope to fall back to: a new
   operation is a new capability, and a new capability's words
   and scope are a reviewer's decision, recorded in this file.
4. The meta tools are prepended from their own declared tuple.
   They are not generated (they travel no operation) and they
   are not hidden — a reader of ``all_tool_specs`` sees the
   whole served catalogue in one list, kinds labelled.

How the checker walks, and why each leg exists
----------------------------------------------
* Coverage, both directions, because B-206's sentence is
  two-directional: an operation without a tool is a capability
  MCP users cannot reach; a tool naming no operation is a
  promise the backend cannot keep. Either alone is drift.
* Uniqueness first, because every later leg compares sets, and
  a duplicated name would let one tool impersonate another in
  a set comparison and pass a check it should fail.
* The scope-mapping leg, because a tool's credential scope is
  only a word until it is mapped: B-205's table says which
  internal scopes a credential's scopes become, and a tool
  demanding a credential that cannot carry its operation would
  be a door that opens onto a refusal — worse, a door whose
  refusal looks like a bug instead of a law.
* The enforcement-table leg, because the call-time guard reads
  ``TOOL_SCOPES`` from the auth module (B-205's seam, kept):
  two tables that can disagree are two sources of truth, so
  the checker makes disagreement a failure by name, per tool.
* The served-surface leg, when a caller passes a built server's
  tool names, because a registry can be perfect on paper while
  the server quietly serves something else; comparing against
  the live list closes the last gap between paper and wire.

The manifest form, and what a verifier does with it
---------------------------------------------------
``tool_manifest`` emits plain JSON-ready dicts — the release
builder stamps them, and the SHA256SUMS + Ed25519 signature
over the ZIP cover them like every other manifest fact. The
verifier (scripts/release_signing.py) recomputes each entry's
description hash and the whole-list digest from the manifest
itself, so a manifest whose descriptions were swapped after
stamping refuses its own verification; comparing a manifest
against a LIVE server's served descriptions (the registry
tests do exactly this against the specs) catches the other
direction — a server whose words moved after its release.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    """One MCP tool, as the registry declares it.

    ``kind`` is ``"operation"`` (the tool travels one registered
    internal operation through the bridge) or ``"meta"`` (the
    tool reports on the server itself; ``operation`` is None).
    ``credential_scope`` is the B-014/B-205 ladder word a caller
    must hold at call time; the server's guard reads it through
    ``gpa.mcp.auth.TOOL_SCOPES``, and the checker below asserts
    the two tables agree — there is one truth, stated here, and
    the auth table is its enforcement copy.
    """

    # The tool's wire name (``gpa_``-prefixed, snake case).
    name: str
    # The internal operation this tool travels, or None (meta).
    operation: str | None
    # The description the server serves for this tool, verbatim.
    description: str
    # The credential scope a call requires (read/draft/publish/admin).
    credential_scope: str
    # "operation" or "meta" — see the class docstring.
    kind: str


# --- The curated annotation layer -------------------------------------------
#
# Operation name -> (tool name, credential scope, description).
# This is the ONLY hand-written part of the catalogue, and it is
# annotation: a name an agent can remember, a scope a reviewer
# can judge, and the exact words an agent will read. Adding an
# operation to the internal API without adding its line here
# fails the checker by name — deliberately, so the catalogue
# grows by decision, never by drift.
#
# How to write an annotation line, for the next editor:
#
# * The tool name is ``gpa_`` + a verb phrase an agent can
#   guess the meaning of before reading the description
#   (``gpa_enqueue_job``, not ``gpa_jobs_enqueue`` — the agent
#   reads names first, module paths second, if ever).
# * The description states, in order: what the tool does, the
#   road it travels (the internal operation it names), and the
#   law that binds the act (draft-never-publication, outbox
#   rows-never-sends, the AI door's kind check). An agent that
#   reads only descriptions should still learn the house law
#   from them — descriptions are instructions, which is
#   precisely why the signed manifest carries them verbatim.
# * The description never promises what the operation refuses:
#   if the handler can refuse (and every handler can), the
#   description names the refusal or stays silent about the
#   outcome — it never guarantees success.
# * The scope is the LEAST credential scope whose mapped
#   internal scopes (B-205's table) include the operation's
#   required scope. Least, not most convenient: the checker
#   enforces "can carry", and review enforces "least that can".
# * One line per operation, in operation-name order, so the
#   diff of a catalogue change reads as the change itself.

ANNOTATIONS: dict[str, tuple[str, str, str]] = {
    "candidates.create": (
        "gpa_create_candidate_draft",
        "draft",
        "Draft one candidate into a group's review queue. A draft, never "
        "a publication: the candidate lands pending, exactly as a human's "
        "draft does, and approval is a separate act under the one "
        "approval law. Kinds are the queue's own (event, task, decision, "
        "question, and their kin).",
    ),
    "events.publish": (
        "gpa_publish_event",
        "publish",
        "Publish one draft event through the internal events.publish "
        "operation — the same operation a human organiser's approval "
        "calls. This tool adds no second road around it, and the "
        "operation's own law (draft state, the service's permission "
        "checks) applies unchanged.",
    ),
    "notify.request": (
        "gpa_request_notification",
        "admin",
        "Write notification rows for one audience — an event's "
        "recipients or one named label — through the internal "
        "notify.request operation. Rows only, under the outbox law: "
        "this never sends; delivery is the notification jobs' work, "
        "and preferences and quiet hours are applied at creation.",
    ),
    "notify.rsvp_promotion": (
        "gpa_notify_rsvp_promotion",
        "admin",
        "Notify a waitlisted member that they have been promoted to a "
        "place, through the internal notify.rsvp_promotion operation — "
        "the same notification the RSVP service writes when a seat "
        "frees, with the same wording and the same audit trail.",
    ),
    "jobs.enqueue": (
        "gpa_enqueue_job",
        "admin",
        "Commit one queued background job through the internal "
        "jobs.enqueue operation. Submission commits, as the direct "
        "form does; the job then runs under the job chassis' claim, "
        "backoff, and dead-letter law, and its progress is read back "
        "through the same job model the human API serves.",
    ),
    "ai.submit_job": (
        "gpa_submit_ai_job",
        "admin",
        "Submit one AI job — extraction, vision, or transcription — "
        "through the internal ai.submit_job operation. Any other job "
        "kind is refused at this door: a caller may not use the AI "
        "door to submit arbitrary background work.",
    ),
    "integrations.emit": (
        "gpa_emit_integration_event",
        "admin",
        "Announce one act to a group's subscribed outbound webhook "
        "endpoints through the internal integrations.emit operation, "
        "in the caller's transaction — either an event's own wire "
        "data, built from its row, or an explicit data payload.",
    ),
}

# The declared meta tools: server facts, no group content, no
# operation travelled. Their scopes are "read" — and even that
# is a real gate (B-205): a credential with no scopes at all
# learns nothing here, not even the operation list's shape.
META_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="gpa_server_info",
        operation=None,
        description=(
            "Report this server's identity and negotiated capabilities: "
            "server name and backend version, the MCP service identity's "
            "key id, the transports this build serves, and the protocol "
            "versions the initialize handshake can negotiate. No group "
            "content exists on this tool."
        ),
        credential_scope="read",
        kind="meta",
    ),
    ToolSpec(
        name="gpa_list_internal_operations",
        operation=None,
        description=(
            "List the internal operations this surface may call — name, "
            "owning module, required scope, one-line summary — together "
            "with the generated tool registry that covers them. An "
            "operation missing here is a capability MCP does not have, "
            "by the bridge's law."
        ),
        credential_scope="read",
        kind="meta",
    ),
)


# --- Generation ---------------------------------------------------------------


def operation_specs(
    annotations: dict[str, tuple[str, str, str]] | None = None,
) -> list[ToolSpec]:
    """Generate one tool spec per registered internal operation.

    Registration is lazy in the internal API (the client's first
    call registers the handlers), so this registers them itself —
    a cold process generates from the real registry, never from
    an empty one. An operation with no annotation raises, naming
    it: generation is total or it does not happen, because a
    silently partial catalogue is exactly what B-206 forbids.
    """
    from gpa.internal import handlers, registry

    handlers.register_all()
    table = ANNOTATIONS if annotations is None else annotations
    specs: list[ToolSpec] = []
    for operation in sorted(registry.OPERATIONS.values(), key=lambda op: op.name):
        annotation = table.get(operation.name)
        if annotation is None:
            raise ValueError(
                f"internal operation '{operation.name}' has no MCP tool "
                "annotation — add its curated line to gpa.mcp.tools.ANNOTATIONS"
            )
        tool_name, scope, description = annotation
        specs.append(
            ToolSpec(
                name=tool_name,
                operation=operation.name,
                description=description,
                credential_scope=scope,
                kind="operation",
            )
        )
    return specs


def all_tool_specs(
    annotations: dict[str, tuple[str, str, str]] | None = None,
) -> list[ToolSpec]:
    """Every tool the server serves: meta tools + operation tools.

    Meta tools first (an agent meets the server before it works),
    then the operation tools in operation-name order — a stable
    order, so manifests and catalogues diff cleanly between
    releases.
    """
    return [*META_TOOLS, *operation_specs(annotations)]


def tool_scopes(specs: list[ToolSpec] | None = None) -> dict[str, str]:
    """Tool name -> required credential scope, from the specs.

    This is the registry's reading of the scope law; the auth
    module's ``TOOL_SCOPES`` is the enforcement copy the call-time
    guard reads, and the checker asserts the two agree exactly.
    """
    return {spec.name: spec.credential_scope for spec in (specs or all_tool_specs())}


# --- The checker ----------------------------------------------------------------


def check_tool_registry(
    specs: list[ToolSpec] | None = None,
    *,
    server_tool_names: set[str] | None = None,
    scopes_table: dict[str, str] | None = None,
) -> list[str]:
    """Every registry failure, each naming its tool or operation.

    An empty list is a sound registry. The legs, in order:

    * every registered internal operation has exactly one tool,
      and every operation tool names a registered operation
      (the two directions of B-206's parity sentence);
    * tool names are unique, meta tools name no operation, and
      operation tools name one;
    * each operation tool's credential scope maps (through
      B-205's table) onto its operation's required internal
      scope;
    * the enforcement scope table (``gpa.mcp.auth.TOOL_SCOPES``,
      or a caller-supplied table) agrees with the specs exactly;
    * when ``server_tool_names`` is given (a built server's live
      tool list), the served tools are exactly the specs — a
      tool the server serves but the registry does not declare
      is the reverse-direction failure, caught at the surface
      where an agent would actually meet it.
    """
    from gpa.internal import handlers, registry

    handlers.register_all()
    specs = all_tool_specs() if specs is None else specs
    failures: list[str] = []

    # Names must be unique before any set comparison means
    # anything: a duplicated name would hide a missing tool
    # behind a same-named one in every set leg below.
    seen: set[str] = set()
    for spec in specs:
        if spec.name in seen:
            failures.append(f"{spec.name}: duplicate MCP tool name in the registry")
        seen.add(spec.name)

    operations = registry.OPERATIONS
    covered: dict[str, str] = {}
    for spec in specs:
        if spec.kind == "meta":
            if spec.operation is not None:
                failures.append(
                    f"{spec.name}: meta tool names operation '{spec.operation}'"
                )
            continue
        if spec.operation is None:
            failures.append(f"{spec.name}: operation tool names no operation")
            continue
        if spec.operation not in operations:
            failures.append(
                f"{spec.name}: names unregistered internal operation "
                f"'{spec.operation}'"
            )
            continue
        if spec.operation in covered:
            failures.append(
                f"{spec.name}: operation '{spec.operation}' already has "
                f"tool '{covered[spec.operation]}'"
            )
        covered[spec.operation] = spec.name
    for operation_name in sorted(operations):
        if operation_name not in covered:
            failures.append(
                f"{operation_name}: internal operation has no MCP tool"
            )

    # The scope-mapping leg: the credential a tool demands must
    # actually be able to carry the operation it travels. The
    # mapping table is B-205's; it is imported inside the check
    # so this module's import never cycles with the auth module
    # (which the server imports alongside this one).
    from gpa.mcp.auth import EXTERNAL_TO_INTERNAL

    for spec in specs:
        if spec.kind != "operation" or spec.operation not in operations:
            continue
        required_internal = operations[spec.operation].required_scope
        mapped = EXTERNAL_TO_INTERNAL.get(spec.credential_scope, frozenset())
        if required_internal not in mapped:
            failures.append(
                f"{spec.name}: credential scope '{spec.credential_scope}' "
                f"does not map onto internal scope '{required_internal}'"
            )

    # The enforcement copy must agree with the registry exactly:
    # a scope stated in one place and enforced from another is
    # two sources of truth, which is what this slice abolishes.
    if scopes_table is None:
        from gpa.mcp.auth import TOOL_SCOPES

        scopes_table = TOOL_SCOPES
    expected_scopes = tool_scopes(specs)
    if dict(scopes_table) != expected_scopes:
        for name in sorted(set(expected_scopes) | set(scopes_table)):
            if scopes_table.get(name) != expected_scopes.get(name):
                failures.append(
                    f"{name}: scope table says "
                    f"'{scopes_table.get(name)}', registry says "
                    f"'{expected_scopes.get(name)}'"
                )

    if server_tool_names is not None and server_tool_names != seen:
        for name in sorted(seen - server_tool_names):
            failures.append(f"{name}: registered tool is not served by the server")
        for name in sorted(server_tool_names - seen):
            failures.append(f"{name}: server serves a tool the registry does not declare")

    return failures


# --- The release manifest -------------------------------------------------------


def description_sha256(description: str) -> str:
    """The SHA-256 of one tool description, exactly as served."""
    return hashlib.sha256(description.encode("utf-8")).hexdigest()


def tool_manifest(specs: list[ToolSpec] | None = None) -> list[dict]:
    """The tool catalogue as release-manifest data.

    One entry per tool: name, operation (null for meta tools),
    credential scope, the full description, and its SHA-256.
    The release builder stamps this list into the signed
    release manifest; :func:`manifest_digest` gives the one
    hash a verifier recomputes to prove no description moved.
    """
    return [
        {
            "name": spec.name,
            "operation": spec.operation,
            "credential_scope": spec.credential_scope,
            "kind": spec.kind,
            "description": spec.description,
            "description_sha256": description_sha256(spec.description),
        }
        for spec in (specs or all_tool_specs())
    ]


def manifest_digest(entries: list[dict]) -> str:
    """One SHA-256 over a manifest's tool entries, canonically.

    Canonical form: the entries as compact JSON with sorted
    keys, in manifest order. Any change — a swapped description,
    a renamed tool, a re-scoped tool — changes this digest,
    which is the whole point of stamping it into a signed
    manifest beside the entries it covers.
    """
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
