"""Operation handlers — the internal API's composition root (B-162).

This module is the ONE place that imports the owning services
to wire them to operation names. It is imported lazily (the
client's first call, or a composition root at startup) because
the services import the client, and an eager import here would
close the circle.

The operations are the five families the roadmap names —
candidate creation, event publication, notification request,
AI job submission, integration call — plus the two supporting
operations the same families need (general job submission,
RSVP-promotion notification). Phase 19 (B-207) adds the first
READ-and-profile family — group reads, the member roster, a
group-settings edit, and person/seat profile reads and edits —
registered so the MCP surface's domain tools (and any future
surface) travel this same door instead of reaching around it.
Every handler:

* takes ids and values from the envelope payload — never ORM
  rows (the wire shape is the in-process shape, B-166);
* re-fetches the rows it needs inside the caller's session;
* keeps the direct call's transaction discipline exactly —
  handlers that replaced non-committing calls do not commit;
  job submission, whose direct form commits, still commits;
* returns plain data: ids and counts, never rows.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from gpa.errors import AppError
from gpa.internal import registry
from gpa.internal.client import CallContext
from gpa.internal.registry import Operation
from gpa.models.events import Event, Rsvp
from gpa.models.groups import Group
from gpa.models.identity import User
from gpa.services import candidates as candidate_service
from gpa.services import events as event_service
from gpa.services import groups as group_service
from gpa.services import identity as identity_service
from gpa.services import jobs as job_service
from gpa.services import notifications as notify_service
from gpa.services import outbound as outbound_service
from gpa.services import extraction as extraction_service
from gpa.services import transcribe as transcribe_service
from gpa.services import vision as vision_service


def _need(payload: dict, *keys: str) -> None:
    """Refuse a payload missing a required key, in the internal
    API's own problem code — a malformed internal call is a bug
    in a caller, and it should fail as loudly as a bad request
    at the external door."""
    missing = [key for key in keys if key not in payload]
    if missing:
        raise AppError(
            "internal_bad_payload",
            detail=f"Payload is missing: {', '.join(missing)}.",
        )


def _group(db: Session, group_id: str | None) -> Group | None:
    """Fetch the payload's group, or refuse a dangling id."""
    if group_id is None:
        return None
    group = db.get(Group, group_id)
    if group is None:
        raise AppError("not_found", detail="That group could not be found.")
    return group


def _moment(value: str | None) -> datetime | None:
    """Parse an ISO-8601 payload moment (``Z`` tolerated)."""
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# --- candidates.create ---------------------------------------------------


def _candidates_create(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Draft one candidate into the review queue (extraction
    module's door; the row's one author is
    ``candidates.create_candidate``). Does not commit."""
    _need(payload, "group_id", "kind", "title", "created_by")
    row = candidate_service.create_candidate(
        db,
        group_id=payload["group_id"],
        kind=payload["kind"],
        title=payload["title"],
        created_by=payload["created_by"],
        status=payload.get("status", "pending"),
        source_id=payload.get("source_id"),
        draft=payload.get("draft"),
        confidence=payload.get("confidence"),
        prompt_name=payload.get("prompt_name", ""),
        prompt_version=payload.get("prompt_version"),
        job_id=payload.get("job_id"),
        flags=payload.get("flags"),
    )
    return {"candidate_id": row.id}


# --- events.publish --------------------------------------------------------


def _events_publish(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Publish one draft event (the organiser's approval act for
    a directly-entered event). Delegates to the events service,
    whose transaction discipline is unchanged."""
    _need(payload, "group_id", "event_id", "actor")
    group = _group(db, payload["group_id"])
    event = event_service.publish_event(
        db, actor_label=payload["actor"], group=group, event_id=payload["event_id"]
    )
    return {"event_id": event.id, "version": event.version}


# --- notify.request --------------------------------------------------------


def _notify_request(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Write notification rows (never sends — the outbox law).

    The audience is either one named recipient or every
    recipient of an event (the notifications module resolves
    that list, preferences and quiet hours included, exactly
    as the direct loops did). Does not commit: the caller's
    transaction carries the rows, as it always did.
    """
    _need(payload, "kind", "subject", "body_text", "audience")
    group = _group(db, payload.get("group_id"))
    audience = payload["audience"]
    recipients: list[dict] = []
    if "event_id" in audience:
        recipients = notify_service.event_recipients(db, audience["event_id"])
    elif "label" in audience:
        user = None
        if audience.get("user_id"):
            user = db.get(User, audience["user_id"])
        recipients = [
            {"user": user, "label": audience["label"], "email": audience.get("email", "")}
        ]
    else:
        raise AppError(
            "internal_bad_payload",
            detail="Audience must name an event_id or a label.",
        )
    created_ids: list[str] = []
    suppressed = 0
    for recipient in recipients:
        row = notify_service.create_notification(
            db,
            group=group,
            recipient_user=recipient["user"],
            recipient_label=recipient["label"],
            recipient_email=recipient["email"],
            kind=payload["kind"],
            subject=payload["subject"],
            body_text=payload["body_text"],
            body_html=payload.get("body_html", ""),
            event_id=payload.get("event_id"),
            urgent=payload.get("urgent", False),
            send_after=_moment(payload.get("send_after")),
            reminder_rule=payload.get("reminder_rule", ""),
            rsvp_id=payload.get("rsvp_id"),
        )
        if row is None:
            suppressed += 1
        else:
            created_ids.append(row.id)
    return {"created_ids": created_ids, "suppressed": suppressed}


def _notify_rsvp_promotion(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Tell a waitlisted member they have a place (the RSVP
    module's one cross-module notification, as an operation)."""
    _need(payload, "group_id", "event_id", "rsvp_id")
    group = _group(db, payload["group_id"])
    event = db.get(Event, payload["event_id"])
    rsvp = db.get(Rsvp, payload["rsvp_id"])
    if event is None or rsvp is None:
        raise AppError("not_found", detail="That event or RSVP could not be found.")
    notify_service.notify_rsvp_promotion(db, group=group, event=event, rsvp=rsvp)
    return {}


# --- jobs.enqueue / ai.submit_job ------------------------------------------

# The job kinds that are AI work: extraction, vision,
# transcription — the kinds whose submission §6A.4 names as
# the ai.submit_job operation. Read from the owning modules so
# a renamed kind cannot drift from this list.
AI_JOB_KINDS = frozenset(
    {
        extraction_service.JOB_KIND,
        vision_service.JOB_KIND,
        transcribe_service.JOB_KIND,
    }
)


def _enqueue(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Commit one queued job row (submission commits — the
    direct form did, so the operation does)."""
    _need(payload, "kind")
    job = job_service.enqueue(
        db,
        ctx.settings,
        kind=payload["kind"],
        payload=payload.get("payload") or {},
        run_at=_moment(payload.get("run_at")),
        max_attempts=payload.get("max_attempts"),
    )
    return {"job_id": job.id}


def _ai_submit_job(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Submit AI work: jobs.enqueue with the kind checked
    against the AI kinds — a caller may not use the AI door to
    submit arbitrary background work."""
    _need(payload, "kind")
    if payload["kind"] not in AI_JOB_KINDS:
        raise AppError(
            "internal_bad_payload",
            detail=f"'{payload['kind']}' is not an AI job kind.",
        )
    return _enqueue(db, payload, ctx)


# --- integrations.emit -------------------------------------------------------


def _integrations_emit(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Announce one act to the group's subscribed endpoints
    (webhook deliveries + their jobs, in the caller's
    transaction — outbound.emit does not commit, and neither
    does this). Event acts let the handler build the wire data
    from the event row, so callers pass facts, not shapes."""
    _need(payload, "group_id", "kind")
    group = _group(db, payload["group_id"])
    if "data" in payload:
        data = payload["data"]
    elif "event_id" in payload:
        event = db.get(Event, payload["event_id"])
        if event is None:
            raise AppError("not_found", detail="That event could not be found.")
        data = outbound_service.event_data(event, **(payload.get("event_extra") or {}))
    else:
        raise AppError(
            "internal_bad_payload",
            detail="Emit needs either data or an event_id.",
        )
    deliveries = outbound_service.emit(db, group=group, kind=payload["kind"], data=data)
    return {"deliveries": len(deliveries)}


# --- groups.get / groups.list_members / groups.update (B-207) -------------
#
# The group family the MCP domain tools stand on. Reads return
# plain serialised facts — the same fields the HTTP API's group
# and roster responses carry — never rows, and never a field the
# API itself withholds (no budget internals, no digest wiring:
# those are operator settings screens, not a roster's business).
# The settings edit is deliberately NARROWER than the HTTP
# door's: only the five plain fields below travel this
# operation, and an unknown field is refused by name rather
# than silently set — a surface that can set any attribute by
# string is a surface that can set role ladders by typo.

# The group-settings fields the groups.update operation carries.
_GROUP_EDITABLE_FIELDS = frozenset(
    {"name", "description", "visibility", "home_timezone", "default_place"}
)


def _group_data(group: Group) -> dict:
    """One group as plain data: the fields every surface shows."""
    return {
        "group_id": group.id,
        "name": group.name,
        "slug": group.slug,
        "description": group.description,
        "visibility": group.visibility,
        "home_timezone": group.home_timezone,
        "default_place": group.default_place,
    }


def _seat_data(seat) -> dict:
    """One agent seat as plain data, profile included (B-202)."""
    return {
        "seat_id": seat.id,
        "group_id": seat.group_id,
        "name": seat.name,
        "role": seat.role,
        "description": seat.description,
        "avatar_url": seat.avatar_url,
    }


def _groups_get(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Read one group by id (the groups service's own fetch,
    whose not_found is the answer for a dangling id)."""
    _need(payload, "group_id")
    return _group_data(group_service.get_group(db, payload["group_id"]))


def _groups_list_members(db: Session, payload: dict, ctx: CallContext) -> dict:
    """The group's full roster: person memberships AND seats.

    One roster, both principal kinds (the seat-equality law,
    B-202): a caller planning with a group needs its people and
    its seats in one answer, each kind labelled as itself —
    persons by membership (role + invite status), seats by
    their seat rows (role + profile).
    """
    _need(payload, "group_id")
    group = group_service.get_group(db, payload["group_id"])
    members = [
        {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": membership.role,
            "status": membership.status,
        }
        for membership, user in group_service.list_members(db, group)
    ]
    seats = [_seat_data(seat) for seat in group_service.list_seats(db, group)]
    return {
        "group_id": group.id,
        "members": members,
        "seats": seats,
        "count": len(members) + len(seats),
    }


def _groups_update(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Edit a group's plain settings through the groups service.

    The service owns the edit, its validation (visibility is
    the closed vocabulary), and its audit line — attributed to
    the payload's ``actor`` label, so a surface's act is
    recorded as that surface's principal, never as the gateway.
    The service commits, as its direct form does.
    """
    _need(payload, "group_id", "actor")
    changes = payload.get("changes") or {}
    unknown = sorted(set(changes) - _GROUP_EDITABLE_FIELDS)
    if unknown:
        raise AppError(
            "internal_bad_payload",
            detail=(
                "groups.update carries only "
                f"{', '.join(sorted(_GROUP_EDITABLE_FIELDS))}; "
                f"refused: {', '.join(unknown)}."
            ),
        )
    if not changes:
        raise AppError(
            "internal_bad_payload", detail="groups.update needs at least one change."
        )
    group = group_service.get_group(db, payload["group_id"])
    updated = group_service.update_group(
        db, actor_label=payload["actor"], group=group, changes=changes
    )
    return _group_data(updated)


# --- profile.get / profile.update (B-207) ----------------------------------
#
# One profile concept, two principal kinds (B-202's law): a
# person's profile is identity's fields (name, timezone,
# locale — never the email, never credentials), and a seat's
# profile is its display face (name, description, avatar URL —
# never its role or scopes, which are administration, not
# profile). The payload names exactly one principal: user_id
# for a person, seat_id + group_id for a seat (a seat exists
# only inside its one group, and another group's seat id is a
# not_found, exactly as at the HTTP door).


def _user_profile(user: User) -> dict:
    """One person's profile as plain data (no credential fields)."""
    return {
        "kind": "user",
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "timezone": user.timezone,
        "locale": user.locale,
    }


def _seat_profile(seat) -> dict:
    """One seat's profile as plain data (no role/scope admin)."""
    return {"kind": "seat", **_seat_data(seat)}


def _profile_target(payload: dict) -> str:
    """Which principal a profile payload names: user | seat.

    Both ids or neither is a malformed call, refused as such —
    a profile operation that guessed its target could edit the
    wrong principal's face, which is precisely the failure this
    family's shape exists to prevent.
    """
    has_user = bool(payload.get("user_id"))
    has_seat = bool(payload.get("seat_id"))
    if has_user == has_seat:
        raise AppError(
            "internal_bad_payload",
            detail="A profile payload names exactly one of user_id or seat_id.",
        )
    return "seat" if has_seat else "user"


def _profile_get(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Read one principal's profile (person or seat, see above)."""
    if _profile_target(payload) == "seat":
        _need(payload, "group_id")
        group = group_service.get_group(db, payload["group_id"])
        return _seat_profile(group_service.get_seat(db, group, payload["seat_id"]))
    return _user_profile(identity_service.get_user(db, payload["user_id"]))


# The per-kind profile fields a profile.update payload may set.
_PROFILE_USER_FIELDS = frozenset({"name", "timezone", "locale"})
_PROFILE_SEAT_FIELDS = frozenset({"name", "description", "avatar_url"})


def _profile_update(db: Session, payload: dict, ctx: CallContext) -> dict:
    """Edit one principal's profile through its owning service.

    Persons: identity.update_profile (only the fields given).
    Seats: groups.update_seat_profile, whose audit line carries
    the payload's ``actor`` label — a seat editing its own face
    is audited as the seat (B-202), and the service refuses an
    emptied name. Fields outside the kind's own set are refused
    by name, for the same reason groups.update refuses its
    unknown fields: profile is a closed vocabulary per kind.
    """
    _need(payload, "actor")
    changes = payload.get("changes") or {}
    if _profile_target(payload) == "seat":
        _need(payload, "group_id")
        unknown = sorted(set(changes) - _PROFILE_SEAT_FIELDS)
        if unknown:
            raise AppError(
                "internal_bad_payload",
                detail=f"A seat profile has no fields: {', '.join(unknown)}.",
            )
        group = group_service.get_group(db, payload["group_id"])
        seat = group_service.update_seat_profile(
            db,
            actor_label=payload["actor"],
            group=group,
            seat_id=payload["seat_id"],
            changes=changes,
        )
        return _seat_profile(seat)
    unknown = sorted(set(changes) - _PROFILE_USER_FIELDS)
    if unknown:
        raise AppError(
            "internal_bad_payload",
            detail=f"A person profile has no fields: {', '.join(unknown)}.",
        )
    user = identity_service.get_user(db, payload["user_id"])
    updated = identity_service.update_profile(
        db,
        user,
        name=changes.get("name"),
        timezone=changes.get("timezone"),
        locale=changes.get("locale"),
    )
    return _user_profile(updated)


def register_all() -> None:
    """Register every operation (idempotent). Called lazily by
    the client's first call and eagerly by composition roots."""
    registry.register(
        Operation(
            "candidates.create",
            "extraction",
            "candidates:write",
            "Draft one candidate into a group's review queue.",
        ),
        _candidates_create,
    )
    registry.register(
        Operation(
            "events.publish",
            "events",
            "events:publish",
            "Publish one draft event.",
        ),
        _events_publish,
    )
    registry.register(
        Operation(
            "notify.request",
            "notifications",
            "notify:write",
            "Write notification rows for an audience; never sends.",
        ),
        _notify_request,
    )
    registry.register(
        Operation(
            "notify.rsvp_promotion",
            "notifications",
            "notify:write",
            "Notify a waitlisted member promoted to a place.",
        ),
        _notify_rsvp_promotion,
    )
    registry.register(
        Operation(
            "jobs.enqueue",
            "jobs",
            "jobs:write",
            "Commit one queued background job.",
        ),
        _enqueue,
    )
    registry.register(
        Operation(
            "ai.submit_job",
            "jobs",
            "ai:submit",
            "Submit one AI job (extraction, vision, transcription).",
        ),
        _ai_submit_job,
    )
    registry.register(
        Operation(
            "integrations.emit",
            "integrations",
            "integrations:write",
            "Announce one act to the group's subscribed endpoints.",
        ),
        _integrations_emit,
    )
    registry.register(
        Operation(
            "groups.get",
            "groups",
            "groups:read",
            "Read one group's plain facts by id.",
        ),
        _groups_get,
    )
    registry.register(
        Operation(
            "groups.list_members",
            "groups",
            "groups:read",
            "List a group's full roster: person memberships and seats.",
        ),
        _groups_list_members,
    )
    registry.register(
        Operation(
            "groups.update",
            "groups",
            "groups:write",
            "Edit a group's plain settings (name, description, visibility, timezone, place).",
        ),
        _groups_update,
    )
    registry.register(
        Operation(
            "profile.get",
            "identity",
            "profile:read",
            "Read one principal's profile (a person's or a seat's).",
        ),
        _profile_get,
    )
    registry.register(
        Operation(
            "profile.update",
            "identity",
            "profile:write",
            "Edit one principal's profile through its owning service.",
        ),
        _profile_update,
    )
