"""Events: minting, direct entry, editing, cancellation (B-049 →
B-051).

An event is born exactly two ways (Doc 04 §6):

- **By approval** — ``mint_from_candidate`` is called by the
  review queue's approve path for event-kind candidates, in the
  approval's own transaction. Approval IS the publish decision,
  so a minted event is born ``published`` and the candidate's
  ``resulting_entity_*`` finally fills in (Phase 3 left it NULL
  on purpose, waiting for this module).
- **By direct organiser entry** — an organiser types the event
  in. That act records a *manual source* first: the entry is
  material too, with the organiser as its provenance, and the
  event links to it like any sourced event.

Editing is optimistic-concurrency PATCH (D-15): the client sends
the ``ETag`` it read as ``If-Match``; a stale match is a 409
``stale_version`` naming the current version — never a silent
overwrite of a co-organiser's work. **Every** field change writes
an ``EventChange`` row in the same transaction; material changes
(time, place, timezone, all-day) also set ``needs_reannounce``.
Events record changes and set that flag — sending the
announcement is reminders' work (a later phase); events never
send anything themselves.
"""

import json
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from gpa.errors import AppError
from gpa.models.events import Event, EventChange, EventSourceLink, Recurrence
from gpa.models.groups import Candidate, Group, role_at_least
from gpa.models.sources import Provenance, SourceChunk
from gpa.services import audit
from gpa.services import sources as source_service

# Fields a PATCH may change. Anything else on the event (status,
# version, the cancellation record) moves only through its own
# named operation — publish, cancel — so no client can smuggle a
# state change past the change-history law.
EDITABLE_FIELDS: tuple[str, ...] = (
    "title", "description", "starts_at", "ends_at", "timezone",
    "all_day", "place_name", "place_address", "lat", "lng",
    "host_label", "host_id", "cost_text", "cost_cents",
    "bring_list", "access_notes", "event_type", "sub_group",
    "capacity",
)

# Changes the group must hear about again (B-050): when, where.
MATERIAL_FIELDS: frozenset[str] = frozenset(
    {"starts_at", "ends_at", "timezone", "all_day", "place_name", "place_address"}
)


def etag_of(event: Event) -> str:
    """The event's ETag: its version, in the wire form ``"v<n>"``."""
    return f'"v{event.version}"'


def _stringify(value) -> str:
    """A field value's change-history form: datetimes as ISO-8601
    UTC (the stored convention), booleans as words, None as empty."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat() + "Z"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def record_change(
    db: Session,
    *,
    event: Event,
    field: str,
    old_value,
    new_value,
    actor_label: str,
    reason: str = "",
) -> EventChange:
    """Append one change row inside the caller's transaction."""
    row = EventChange(
        event_id=event.id,
        field=field,
        old_value=_stringify(old_value),
        new_value=_stringify(new_value),
        changed_by=actor_label,
        reason=reason,
    )
    db.add(row)
    return row


def get_event(db: Session, group: Group, event_id: str) -> Event:
    """One event of this group, or 404 (another group's event is
    indistinguishable from a missing one)."""
    event = db.get(Event, event_id)
    if event is None or event.group_id != group.id:
        raise AppError("not_found", detail="That event could not be found.")
    return event


def visible_to(event: Event, role: str | None) -> bool:
    """The bright line, as a predicate (B-049): drafts are visible
    to organisers and above only; everyone else must not be able
    to tell a draft exists. Published and cancelled are visible to
    every member."""
    if event.status == "draft":
        return role is not None and role_at_least(role, "organiser")
    return role is not None


def get_visible_event(db: Session, group: Group, event_id: str, role: str | None) -> Event:
    """``get_event`` plus the bright line: a draft asked for by a
    non-organiser is a 404, exactly as if it did not exist."""
    event = get_event(db, group, event_id)
    if not visible_to(event, role):
        raise AppError("not_found", detail="That event could not be found.")
    return event


def list_events(
    db: Session, group: Group, *, role: str | None, status: str | None = None
) -> list[Event]:
    """The group's events, soonest first. Drafts ride along only
    for organisers (the bright line again); a ``status`` filter
    narrows further but can never widen visibility."""
    query = db.query(Event).filter(Event.group_id == group.id)
    rows = query.order_by(Event.starts_at, Event.id).all()
    out = []
    for event in rows:
        if not visible_to(event, role):
            continue
        if status and event.status != status:
            continue
        out.append(event)
    return out


# ------------------------------------------------------------------
# Minting (B-049)
# ------------------------------------------------------------------


def _draft_field(draft: dict, name: str):
    """A draft field's value: the top-level mirror first (the
    shape extraction writes), then the fields map's value."""
    if draft.get(name) is not None:
        return draft[name]
    fields = draft.get("fields", {})
    entry = fields.get(name, {}) if isinstance(fields, dict) else {}
    return entry.get("value") if isinstance(entry, dict) else None


def _draft_local_start(draft: dict) -> tuple[datetime | None, bool]:
    """The draft's start as a LOCAL naive datetime, plus whether
    it is date-only (→ an all-day event). Reads, in order: the
    ``starts_at`` mirror (date + resolved time), ``starts_date``,
    then the fields map's resolved date/time. (None, False) when
    the draft never resolved a start — minting refuses those."""
    mirror = draft.get("starts_at")
    if isinstance(mirror, str) and "T" in mirror:
        try:
            return datetime.fromisoformat(mirror), False
        except ValueError:
            pass
    date_text = draft.get("starts_date")
    fields = draft.get("fields", {})
    starts_entry = fields.get("starts", {}) if isinstance(fields, dict) else {}
    if not date_text and isinstance(starts_entry, dict):
        date_text = starts_entry.get("resolved_date")
    if not date_text:
        return None, False
    try:
        day = datetime.fromisoformat(str(date_text)).date()
    except ValueError:
        return None, False
    time_text = None
    if isinstance(starts_entry, dict):
        time_text = starts_entry.get("resolved_time")
    if time_text:
        try:
            return datetime.combine(day, time.fromisoformat(str(time_text))), False
        except ValueError:
            pass
    return datetime.combine(day, time(0, 0)), True


def _draft_local_end(draft: dict, start_local: datetime, all_day: bool) -> datetime:
    """The draft's end, or the standing default when the source
    named none: a day for all-day events, two hours for timed
    ones (recorded as a decision in the memory map — a source
    that states an end always wins over the default)."""
    mirror = draft.get("ends_at")
    if isinstance(mirror, str) and "T" in mirror:
        try:
            return datetime.fromisoformat(mirror)
        except ValueError:
            pass
    date_text = draft.get("ends_date")
    fields = draft.get("fields", {})
    ends_entry = fields.get("ends", {}) if isinstance(fields, dict) else {}
    if not date_text and isinstance(ends_entry, dict):
        date_text = ends_entry.get("resolved_date")
    if date_text:
        try:
            day = datetime.fromisoformat(str(date_text)).date()
        except ValueError:
            day = None
        if day is not None:
            time_text = ends_entry.get("resolved_time") if isinstance(ends_entry, dict) else None
            if time_text:
                try:
                    return datetime.combine(day, time.fromisoformat(str(time_text)))
                except ValueError:
                    pass
            return datetime.combine(day, time(0, 0)) + (timedelta(days=1) if all_day else timedelta(hours=2))
    return start_local + (timedelta(days=1) if all_day else timedelta(hours=2))


def _local_to_utc(local_naive: datetime, tz: ZoneInfo) -> datetime:
    """One local wall time → its UTC instant (naive, D-21)."""
    return local_naive.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)


def mint_from_candidate(
    db: Session, *, group: Group, candidate: Candidate, actor_label: str
) -> Event | None:
    """Mint the entity an approved candidate becomes (B-049).

    Event-kind candidates mint an Event, born published — the
    approval was the publish decision. Other kinds return None:
    their entities belong to later phases (tasks/decisions/
    questions, Phase 7), and approval for them stays a recorded
    decision only, exactly as Phase 3 stated. Called inside the
    approval's transaction; this function never commits.
    """
    if candidate.kind != "event":
        return None
    try:
        draft = json.loads(candidate.draft_json or "{}")
    except json.JSONDecodeError:
        draft = {}
    if not isinstance(draft, dict):
        draft = {}
    start_local, all_day = _draft_local_start(draft)
    if start_local is None:
        raise AppError(
            "validation_error",
            detail=(
                "That draft has no resolved start date, so it cannot "
                "become an event yet — edit the draft to give it a date first."
            ),
        )
    tz = ZoneInfo(group.home_timezone or "UTC")
    end_local = _draft_local_end(draft, start_local, all_day)
    event = Event(
        group_id=group.id,
        title=str(_draft_field(draft, "title") or candidate.title or "Untitled event")[:240],
        description=str(_draft_field(draft, "description") or ""),
        starts_at=_local_to_utc(start_local, tz),
        ends_at=_local_to_utc(end_local, tz),
        timezone=group.home_timezone or "UTC",
        all_day=all_day,
        place_name=str(_draft_field(draft, "place") or "")[:240],
        host_label=str(_draft_field(draft, "host") or "")[:160],
        cost_text=str(_draft_field(draft, "cost") or "")[:120],
        bring_list=str(_draft_field(draft, "bring") or ""),
        status="published",
        candidate_id=candidate.id,
        created_by=actor_label,
    )
    db.add(event)
    db.flush()  # the event id must exist before links point at it
    # The supporting sources ride along: one link per provenance
    # row (field + quote), so the published event can always
    # answer "where did this come from?" When the source was
    # deleted first, its provenance went with it (B-023) — the
    # candidate's tombstone link is then the whole record.
    provenance_rows = (
        db.query(Provenance).filter(Provenance.candidate_id == candidate.id).all()
    )
    linked_sources: set[str] = set()
    for row in provenance_rows:
        chunk = db.get(SourceChunk, row.chunk_id)
        if chunk is None:
            continue
        db.add(
            EventSourceLink(
                event_id=event.id, source_id=chunk.source_id,
                field=row.field, quote=row.quote,
            )
        )
        linked_sources.add(chunk.source_id)
    if candidate.source_id and candidate.source_id not in linked_sources:
        db.add(
            EventSourceLink(
                event_id=event.id, source_id=candidate.source_id, field="", quote=""
            )
        )
    candidate.resulting_entity_type = "event"
    candidate.resulting_entity_id = event.id
    audit.record(
        db, actor=actor_label, action="event.minted",
        group_id=group.id, entity_type="event", entity_id=event.id,
        detail={"candidate_id": candidate.id},
    )
    return event


# ------------------------------------------------------------------
# Direct organiser entry (B-049)
# ------------------------------------------------------------------


def create_event(
    db: Session, *, actor_label: str, group: Group, data: dict
) -> Event:
    """Direct organiser entry: record the manual source, then the
    event it supports — the entry is material with a person as
    its provenance, so a hand-typed event answers "where did
    this come from?" exactly like an extracted one.

    ``data`` is the validated create payload; starts_at/ends_at
    arrive as UTC-naive datetimes (the schema layer owns the
    wire→UTC conversion)."""
    if data.get("status", "published") not in ("draft", "published"):
        raise AppError(
            "validation_error",
            detail="A new event's status is 'draft' or 'published'.",
        )
    if data["ends_at"] <= data["starts_at"]:
        raise AppError(
            "validation_error",
            detail="An event must end after it starts.",
        )
    starts_at: datetime = data["starts_at"]
    ends_at: datetime = data["ends_at"]
    tz = ZoneInfo(data.get("timezone") or group.home_timezone or "UTC")
    start_local = starts_at.replace(tzinfo=timezone.utc).astimezone(tz).replace(tzinfo=None)
    summary = (
        f"{data['title']} — {start_local.isoformat()} ({tz.key})"
        + (f", {data['place_name']}" if data.get("place_name") else "")
        + f". Entered directly by {actor_label}."
    )
    source = source_service.create_source(
        db,
        actor_label=actor_label,
        group=group,
        kind="manual",
        title=f"Direct entry: {data['title']}"[:240],
        granted_scope="direct organiser entry",
        chunks=[{"text": summary, "sender": actor_label}],
    )
    event = Event(
        group_id=group.id,
        title=data["title"],
        description=data.get("description", ""),
        starts_at=starts_at,
        ends_at=ends_at,
        timezone=data.get("timezone") or group.home_timezone or "UTC",
        all_day=bool(data.get("all_day", False)),
        place_name=data.get("place_name", ""),
        place_address=data.get("place_address", ""),
        lat=data.get("lat"),
        lng=data.get("lng"),
        host_label=data.get("host_label", ""),
        host_id=data.get("host_id"),
        cost_text=data.get("cost_text", ""),
        cost_cents=data.get("cost_cents"),
        bring_list=data.get("bring_list", ""),
        access_notes=data.get("access_notes", ""),
        event_type=data.get("event_type", ""),
        sub_group=data.get("sub_group", ""),
        capacity=data.get("capacity"),
        status=data.get("status", "published"),
        created_by=actor_label,
    )
    db.add(event)
    db.flush()
    db.add(EventSourceLink(event_id=event.id, source_id=source.id, field="", quote=summary))
    audit.record(
        db, actor=actor_label, action="event.created",
        group_id=group.id, entity_type="event", entity_id=event.id,
        detail={"source_id": source.id, "status": event.status},
    )
    db.commit()
    return event


# ------------------------------------------------------------------
# Editing + change history (B-050), cancellation + clone (B-051)
# ------------------------------------------------------------------


def _parse_if_match(if_match: str | None) -> int:
    """The version an If-Match header names (``"v3"``, ``v3``, or a
    bare ``3`` are all the same claim). Missing or unreadable is a
    client error in plain words — an update without a version
    claim is exactly the lost-update D-15 exists to prevent."""
    if if_match is None or not str(if_match).strip():
        raise AppError(
            "validation_error",
            detail="Updates need an If-Match header carrying the version you read.",
        )
    text = str(if_match).strip().strip('"')
    if text.startswith("v"):
        text = text[1:]
    try:
        return int(text)
    except ValueError:
        raise AppError(
            "validation_error",
            detail="That If-Match header does not name a version.",
        )


def update_event(
    db: Session,
    *,
    actor_label: str,
    group: Group,
    event_id: str,
    changes: dict,
    if_match: str | None,
    reason: str = "",
) -> Event:
    """Apply a PATCH under optimistic concurrency (B-050, D-15).

    Every field that actually changes writes an EventChange row;
    a material change sets needs_reannounce. A patch that changes
    nothing is a no-op success (no version bump, no history
    noise). Cancelled events refuse edits — a cancellation is
    reversed by cloning forward, not by quietly un-cancelling."""
    event = get_event(db, group, event_id)
    claimed = _parse_if_match(if_match)
    if claimed != event.version:
        raise AppError(
            "stale_version",
            detail=(
                f"This event has changed since you read it — it is now "
                f"at version {event.version}. Read it again and re-apply "
                f"your change to the current version."
            ),
        )
    if event.status == "cancelled":
        raise AppError("conflict", detail="A cancelled event cannot be edited.")
    changed_fields: list[str] = []
    for field_name in EDITABLE_FIELDS:
        if field_name not in changes:
            continue
        new_value = changes[field_name]
        old_value = getattr(event, field_name)
        if new_value == old_value:
            continue
        record_change(
            db, event=event, field=field_name, old_value=old_value,
            new_value=new_value, actor_label=actor_label, reason=reason,
        )
        setattr(event, field_name, new_value)
        changed_fields.append(field_name)
    if changed_fields:
        if MATERIAL_FIELDS & set(changed_fields):
            event.needs_reannounce = True
        event.version += 1
        audit.record(
            db, actor=actor_label, action="event.updated",
            group_id=group.id, entity_type="event", entity_id=event.id,
            detail={"fields": changed_fields},
        )
    db.commit()
    return event


def list_changes(db: Session, group: Group, event_id: str) -> list[EventChange]:
    """One event's change feed: complete, in the order the
    changes happened (B-050's acceptance)."""
    event = get_event(db, group, event_id)
    return (
        db.query(EventChange)
        .filter(EventChange.event_id == event.id)
        .order_by(EventChange.created_at, EventChange.id)
        .all()
    )


def publish_event(
    db: Session, *, actor_label: str, group: Group, event_id: str
) -> Event:
    """Draft → published: the organiser's own version of the
    approval act for a directly-entered event."""
    event = get_event(db, group, event_id)
    if event.status == "published":
        raise AppError("conflict", detail="That event is already published.")
    if event.status == "cancelled":
        raise AppError("conflict", detail="A cancelled event cannot be published.")
    record_change(
        db, event=event, field="status", old_value=event.status,
        new_value="published", actor_label=actor_label,
    )
    event.status = "published"
    event.version += 1
    audit.record(
        db, actor=actor_label, action="event.published",
        group_id=group.id, entity_type="event", entity_id=event.id,
    )
    db.commit()
    return event


def cancel_event(
    db: Session, *, actor_label: str, group: Group, event_id: str, reason: str = ""
) -> Event:
    """Cancel, with the reason in the canceller's words (B-051).

    Cancellation is a state, never a disappearance: the row, its
    change history, and its feed presence all stay — every
    surface that showed the event live now shows it *cancelled*.
    The notifying state is set here (needs_reannounce + the
    change row reminders read); events send nothing themselves."""
    event = get_event(db, group, event_id)
    if event.status == "cancelled":
        raise AppError("conflict", detail="That event is already cancelled.")
    from gpa.models.identity import now_utc

    record_change(
        db, event=event, field="status", old_value=event.status,
        new_value="cancelled", actor_label=actor_label, reason=reason,
    )
    event.status = "cancelled"
    event.cancelled_reason = reason
    event.cancelled_at = now_utc()
    event.needs_reannounce = True
    event.version += 1
    audit.record(
        db, actor=actor_label, action="event.cancelled",
        group_id=group.id, entity_type="event", entity_id=event.id,
        detail={"reason": reason},
    )
    db.commit()
    return event


def clone_event(
    db: Session, *, actor_label: str, group: Group, event_id: str
) -> Event:
    """Clone last time's event (B-051): structure copies — title,
    times, place, lists, capacity, the recurrence rule — and
    people's answers never do: no RSVPs, no discussion, no change
    history. The clone is born a draft with fresh dates to set;
    the old series' exceptions do NOT copy (they name the old
    series' dates, not the new one's)."""
    source = get_event(db, group, event_id)
    clone = Event(
        group_id=group.id,
        title=source.title,
        description=source.description,
        starts_at=source.starts_at,
        ends_at=source.ends_at,
        timezone=source.timezone,
        all_day=source.all_day,
        place_name=source.place_name,
        place_address=source.place_address,
        lat=source.lat,
        lng=source.lng,
        host_label=source.host_label,
        host_id=source.host_id,
        cost_text=source.cost_text,
        cost_cents=source.cost_cents,
        bring_list=source.bring_list,
        access_notes=source.access_notes,
        event_type=source.event_type,
        sub_group=source.sub_group,
        capacity=source.capacity,
        flyer_id=source.flyer_id,
        status="draft",
        created_by=actor_label,
    )
    db.add(clone)
    db.flush()
    recurrence = (
        db.query(Recurrence).filter(Recurrence.event_id == source.id).one_or_none()
    )
    if recurrence is not None:
        db.add(Recurrence(event_id=clone.id, rrule=recurrence.rrule, exceptions_json="[]"))
    audit.record(
        db, actor=actor_label, action="event.cloned",
        group_id=group.id, entity_type="event", entity_id=clone.id,
        detail={"from_event_id": source.id},
    )
    db.commit()
    return clone
