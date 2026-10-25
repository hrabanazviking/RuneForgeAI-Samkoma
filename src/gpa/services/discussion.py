"""Event discussion — threads v1 (roadmap B-060).

Threads and comments under an event: post, edit your own,
delete your own; organisers moderate by HIDING, with the audit
trail saying who hid what and when. Moderation is state, never
erasure: a hidden comment keeps its body for organisers; an
author's delete is a tombstone that keeps the thread's shape.

The machinery is deliberately polymorphic (``Thread.parent_*``)
— Phase 7 generalises the same tables to tasks, decisions, and
polls (Doc 04 §6); this phase wires the event parent only.

New comments also speak on the group's SSE stream as
``comment.created`` frames (services/stream.py polls the same
durable tables — there is no in-memory bus to lose them).
"""

from sqlalchemy.orm import Session

from gpa.errors import AppError
from gpa.models.events import Comment, Thread
from gpa.models.groups import Group, role_at_least
from gpa.models.identity import now_utc
from gpa.services import audit
from gpa.services import events as event_service


def get_or_create_thread(
    db: Session, *, group: Group, event, actor_label: str
) -> Thread:
    """The event's discussion thread (one per event in v1),
    created by the first poster."""
    thread = (
        db.query(Thread)
        .filter(
            Thread.group_id == group.id,
            Thread.parent_type == "event",
            Thread.parent_id == event.id,
        )
        .order_by(Thread.created_at, Thread.id)
        .first()
    )
    if thread is None:
        thread = Thread(
            group_id=group.id, parent_type="event", parent_id=event.id,
            title="", created_by=actor_label,
        )
        db.add(thread)
        db.flush()
    return thread


def _get_comment(db: Session, group: Group, comment_id: str) -> Comment:
    """One comment of this group (through its thread), or 404."""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise AppError("not_found", detail="That comment could not be found.")
    thread = db.get(Thread, comment.thread_id)
    if thread is None or thread.group_id != group.id:
        raise AppError("not_found", detail="That comment could not be found.")
    return comment


def post_comment(
    db: Session,
    *,
    author_label: str,
    author_user_id: str | None,
    author_seat_id: str | None,
    group: Group,
    event_id: str,
    viewer_role: str | None,
    body: str,
) -> Comment:
    """Post to the event's thread. The event must be visible to
    the poster (a draft's discussion is organiser-only, like the
    draft itself)."""
    if not body or not body.strip():
        raise AppError("validation_error", detail="A comment needs words.")
    event = event_service.get_visible_event(db, group, event_id, viewer_role)
    thread = get_or_create_thread(db, group=group, event=event, actor_label=author_label)
    comment = Comment(
        thread_id=thread.id,
        author_label=author_label,
        author_user_id=author_user_id,
        author_seat_id=author_seat_id,
        body=body,
    )
    db.add(comment)
    db.flush()
    audit.record(
        db, actor=author_label, action="comment.created",
        group_id=group.id, entity_type="event", entity_id=event.id,
        detail={"comment_id": comment.id},
    )
    db.commit()
    return comment


def list_comments(
    db: Session, *, group: Group, event_id: str, viewer_role: str | None
) -> list[Comment]:
    """The event's discussion, oldest first.

    What a viewer sees is role-shaped: members see live comments
    only — hidden ones are simply absent, deleted ones too.
    Organisers see everything, flagged: the hidden body (their
    moderation may need it) and the tombstones."""
    event = event_service.get_visible_event(db, group, event_id, viewer_role)
    thread_ids = [
        row.id
        for row in db.query(Thread)
        .filter(
            Thread.group_id == group.id,
            Thread.parent_type == "event",
            Thread.parent_id == event.id,
        )
        .all()
    ]
    if not thread_ids:
        return []
    rows = (
        db.query(Comment)
        .filter(Comment.thread_id.in_(thread_ids))
        .order_by(Comment.created_at, Comment.id)
        .all()
    )
    if viewer_role is not None and role_at_least(viewer_role, "organiser"):
        return rows
    return [row for row in rows if row.hidden_at is None and row.deleted_at is None]


def _is_author(comment: Comment, user_id: str | None, seat_id: str | None) -> bool:
    if seat_id is not None:
        return comment.author_seat_id == seat_id
    return user_id is not None and comment.author_user_id == user_id


def edit_comment(
    db: Session,
    *,
    author_label: str,
    user_id: str | None,
    seat_id: str | None,
    group: Group,
    comment_id: str,
    body: str,
) -> Comment:
    """Edit your own words. Only the author — an organiser's
    road for other people's words is hiding, never rewriting."""
    if not body or not body.strip():
        raise AppError("validation_error", detail="A comment needs words.")
    comment = _get_comment(db, group, comment_id)
    if comment.deleted_at is not None:
        raise AppError("conflict", detail="A deleted comment cannot be edited.")
    if not _is_author(comment, user_id, seat_id):
        raise AppError("forbidden", detail="You can only edit your own comments.")
    comment.body = body
    comment.edited_at = now_utc()
    audit.record(
        db, actor=author_label, action="comment.edited",
        group_id=group.id, entity_type="comment", entity_id=comment.id,
    )
    db.commit()
    return comment


def delete_comment(
    db: Session,
    *,
    author_label: str,
    user_id: str | None,
    seat_id: str | None,
    group: Group,
    comment_id: str,
) -> Comment:
    """Delete your own comment: a tombstone — the row and its
    place in the thread stay, the words go."""
    comment = _get_comment(db, group, comment_id)
    if comment.deleted_at is not None:
        raise AppError("conflict", detail="That comment is already deleted.")
    if not _is_author(comment, user_id, seat_id):
        raise AppError("forbidden", detail="You can only delete your own comments.")
    comment.body = ""
    comment.deleted_at = now_utc()
    audit.record(
        db, actor=author_label, action="comment.deleted",
        group_id=group.id, entity_type="comment", entity_id=comment.id,
    )
    db.commit()
    return comment


def set_hidden(
    db: Session,
    *,
    actor_label: str,
    group: Group,
    comment_id: str,
    hidden: bool,
) -> Comment:
    """Organiser moderation (the router holds the role door):
    hide — the comment vanishes from members' view and stays,
    flagged, for organisers — or unhide it back. Both are
    audited with the moderator's name: moderation that cannot
    be reviewed is just power."""
    comment = _get_comment(db, group, comment_id)
    if hidden and comment.hidden_at is None:
        comment.hidden_at = now_utc()
        comment.hidden_by = actor_label
        action = "comment.hidden"
    elif not hidden and comment.hidden_at is not None:
        comment.hidden_at = None
        comment.hidden_by = None
        action = "comment.unhidden"
    else:
        return comment
    audit.record(
        db, actor=actor_label, action=action,
        group_id=group.id, entity_type="comment", entity_id=comment.id,
        detail={"author": comment.author_label},
    )
    db.commit()
    return comment
