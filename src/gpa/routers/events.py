"""Event routes (roadmap B-049 → B-052).

The write doors and the single-event reads of the events module.
Reads are member+ with the bright line enforced in the service
(a draft is a 404 to anyone below organiser); writes are
organiser+ with the publish scope for key callers. Calendar-wide
reads (agenda / month / tonight / feeds) live in
routers/calendar.py; the .ics doors in the same file keep this
one about the event itself.
"""

from fastapi import APIRouter, Depends, Header, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from gpa.db import get_db
from gpa.deps import GroupContext, Principal, require_group_role, require_scope
from gpa.models.groups import role_at_least
from gpa.schemas.events import (
    CancelRequest,
    EventChangeResponse,
    EventCreateRequest,
    EventPatchRequest,
    EventResponse,
    ExceptionRequest,
    OccurrenceResponse,
    RecurrenceRequest,
    RecurrenceResponse,
    change_row,
    project_event,
    to_utc_naive,
)
from gpa.services import events as event_service
from gpa.services import recurrence as recurrence_service

router = APIRouter(prefix="/api/v1/groups", tags=["events"])


def _level_for(context: GroupContext) -> str:
    """The projection level a caller reads at (B-059)."""
    if context.role is not None and role_at_least(context.role, "organiser"):
        return "organiser"
    return "member"


@router.post("/{group_id}/events", response_model=EventResponse, status_code=201)
def create_event(
    body: EventCreateRequest,
    response: Response,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Direct organiser entry (B-049): the entry records a manual
    source, and the event is born in the asked-for state (draft
    or published — drafts reach no feed)."""
    data = body.model_dump()
    data["starts_at"] = to_utc_naive(body.starts_at)
    data["ends_at"] = to_utc_naive(body.ends_at)
    event = event_service.create_event(
        db, actor_label=principal.label, group=context.group, data=data
    )
    response.headers["ETag"] = event_service.etag_of(event)
    return project_event(event, "organiser")


@router.get("/{group_id}/events", response_model=list[EventResponse])
def list_events(
    status: str | None = None,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """The group's events, soonest first, at the caller's
    projection level. Drafts appear only for organisers."""
    rows = event_service.list_events(
        db, context.group, role=context.role, status=status
    )
    level = _level_for(context)
    return [project_event(event, level) for event in rows]


@router.get("/{group_id}/events/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    response: Response,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """One event. A draft asked for by a non-organiser is a 404 —
    the bright line (B-049) is existence-level, not field-level."""
    event = event_service.get_visible_event(
        db, context.group, event_id, context.role
    )
    response.headers["ETag"] = event_service.etag_of(event)
    level = _level_for(context)
    links = None
    if level == "organiser":
        from gpa.services import ical as ical_service

        links = ical_service.event_links(event)
        links["ics_download"] = (
            f"/api/v1/groups/{context.group.id}/events/{event.id}/ics"
        )
    return project_event(event, level, links=links)


@router.patch("/{group_id}/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    body: EventPatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Edit an event (B-050, D-15): If-Match carries the version
    read; every changed field lands in the change history; the
    response carries the new ETag."""
    changes = body.model_dump(exclude_unset=True)
    reason = changes.pop("reason", "")
    for field_name in ("starts_at", "ends_at"):
        if changes.get(field_name) is not None:
            changes[field_name] = to_utc_naive(changes[field_name])
    event = event_service.update_event(
        db, actor_label=principal.label, group=context.group,
        event_id=event_id, changes=changes, if_match=if_match, reason=reason,
    )
    response.headers["ETag"] = event_service.etag_of(event)
    return project_event(event, "organiser")


@router.get(
    "/{group_id}/events/{event_id}/changes",
    response_model=list[EventChangeResponse],
)
def list_changes(
    event_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """The event's change feed — complete, in order (B-050)."""
    event_service.get_visible_event(db, context.group, event_id, context.role)
    rows = event_service.list_changes(db, context.group, event_id)
    return [change_row(row) for row in rows]


@router.post("/{group_id}/events/{event_id}/publish", response_model=EventResponse)
def publish_event(
    event_id: str,
    response: Response,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Draft → published (B-049's bright line, crossed on purpose)."""
    event = event_service.publish_event(
        db, actor_label=principal.label, group=context.group, event_id=event_id
    )
    response.headers["ETag"] = event_service.etag_of(event)
    return project_event(event, "organiser")


@router.post("/{group_id}/events/{event_id}/cancel", response_model=EventResponse)
def cancel_event(
    event_id: str,
    body: CancelRequest,
    response: Response,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Cancel with a reason (B-051): the event stays, marked
    cancelled everywhere it was ever shown."""
    event = event_service.cancel_event(
        db, actor_label=principal.label, group=context.group,
        event_id=event_id, reason=body.reason,
    )
    response.headers["ETag"] = event_service.etag_of(event)
    return project_event(event, "organiser")


@router.post("/{group_id}/events/{event_id}/clone", response_model=EventResponse, status_code=201)
def clone_event(
    event_id: str,
    response: Response,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Clone last time's event (B-051): structure copies, RSVPs
    and discussion never do; the clone is born a draft."""
    event = event_service.clone_event(
        db, actor_label=principal.label, group=context.group, event_id=event_id
    )
    response.headers["ETag"] = event_service.etag_of(event)
    return project_event(event, "organiser")


@router.get(
    "/{group_id}/events/{event_id}/occurrences",
    response_model=list[OccurrenceResponse],
)
def list_occurrences(
    event_id: str,
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """This event's occurrences in a window (B-052): the API
    returns occurrences, never the rule, so the frontend does
    zero date maths. ``from``/``to`` are ISO datetimes; the
    default window is the event's start through +92 days."""
    from datetime import datetime, timedelta

    from gpa.errors import AppError
    from gpa.schemas.events import occurrence_view

    event = event_service.get_visible_event(
        db, context.group, event_id, context.role
    )
    try:
        window_start = (
            datetime.fromisoformat(from_.replace("Z", "+00:00"))
            if from_ else None
        )
        window_end = (
            datetime.fromisoformat(to.replace("Z", "+00:00")) if to else None
        )
    except ValueError:
        raise AppError("validation_error", detail="from/to must be ISO datetimes.")
    from gpa.schemas.events import to_utc_naive

    start = to_utc_naive(window_start) if window_start else event.starts_at - timedelta(days=1)
    end = to_utc_naive(window_end) if window_end else event.starts_at + timedelta(days=92)
    if end <= start:
        raise AppError("validation_error", detail="The window must end after it starts.")
    if end - start > timedelta(days=731):
        raise AppError("validation_error", detail="Occurrence windows are at most two years.")
    recurrence = recurrence_service.get_recurrence(db, event_id)
    occurrences = recurrence_service.expand(
        starts_at_utc=event.starts_at, ends_at_utc=event.ends_at,
        tz_name=event.timezone,
        rrule_text=recurrence.rrule if recurrence else None,
        recurrence=recurrence,
        window_start_utc=start, window_end_utc=end,
    )
    return [occurrence_view(event, occ) for occ in occurrences]


# ------------------------------------------------------------------
# Facebook Event drafts (B-058) — drafts only, never a post
# ------------------------------------------------------------------


class FacebookDraftResponse(BaseModel):
    """The draft as the organiser receives it: Meta-shaped
    payload, a copy-ready text block, and the cover suggestion."""

    payload: dict
    copy_text: str
    cover: dict | None = None


@router.get(
    "/{group_id}/events/{event_id}/facebook-draft",
    response_model=FacebookDraftResponse,
)
def facebook_draft(
    event_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    db: Session = Depends(get_db),
):
    """Build the Facebook Event DRAFT for a published event
    (B-058). Nothing is created on Facebook — creating the real
    event is the Phase 12 integration with a human pressing the
    button, because posting as a person/page is an outward act."""
    from gpa.services import facebook as facebook_service

    event = event_service.get_event(db, context.group, event_id)
    return facebook_service.build_draft(db, event)


# ------------------------------------------------------------------
# Recurrence (B-052)
# ------------------------------------------------------------------


def _recurrence_response(event_id: str, row) -> RecurrenceResponse:
    return RecurrenceResponse(
        event_id=event_id,
        rrule=row.rrule,
        exceptions=recurrence_service.load_exceptions(row),
    )


@router.get(
    "/{group_id}/events/{event_id}/recurrence", response_model=RecurrenceResponse
)
def get_recurrence(
    event_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """The series rule + exceptions for one event (404 when the
    event does not repeat)."""
    event_service.get_visible_event(db, context.group, event_id, context.role)
    row = recurrence_service.get_recurrence(db, event_id)
    if row is None:
        from gpa.errors import AppError

        raise AppError("not_found", detail="That event does not repeat.")
    return _recurrence_response(event_id, row)


@router.put(
    "/{group_id}/events/{event_id}/recurrence", response_model=RecurrenceResponse
)
def set_recurrence(
    event_id: str,
    body: RecurrenceRequest,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Set or replace the series rule (B-052). The rule is parsed
    before it is stored — an unexpandable rule is refused here,
    in plain words, never discovered later by a reader."""
    event = event_service.get_event(db, context.group, event_id)
    row = recurrence_service.set_recurrence(
        db, actor_label=principal.label, group=context.group, event=event,
        rrule_text=body.rrule, exceptions=body.exceptions,
    )
    return _recurrence_response(event_id, row)


@router.post(
    "/{group_id}/events/{event_id}/recurrence/exceptions",
    response_model=RecurrenceResponse,
)
def add_exception(
    event_id: str,
    body: ExceptionRequest,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Move or cancel ONE occurrence (B-052): the rule stands;
    this happening is the exception."""
    event = event_service.get_event(db, context.group, event_id)
    row = recurrence_service.add_exception(
        db, actor_label=principal.label, group=context.group, event=event,
        original_start=body.original_start, moved_to=body.moved_to,
        cancelled=body.cancelled,
    )
    return _recurrence_response(event_id, row)


@router.delete("/{group_id}/events/{event_id}/recurrence", status_code=204)
def delete_recurrence(
    event_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Remove the rule: the event becomes a one-off (B-052)."""
    event = event_service.get_event(db, context.group, event_id)
    recurrence_service.delete_recurrence(
        db, actor_label=principal.label, group=context.group, event=event
    )
    return Response(status_code=204)
