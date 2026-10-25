"""Discussion routes (roadmap B-060).

Threads v1 under events: list, post, edit/delete your own, and
organiser moderation (hide/unhide — audited in the service).
Reads and posts are member+; posting rides the draft scope for
key callers (writing words is a draft-class act); hiding is
organiser+ behind the publish scope.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gpa.db import get_db
from gpa.deps import GroupContext, Principal, require_group_role, require_scope
from gpa.models.events import Thread
from gpa.schemas.events import (
    CommentCreateRequest,
    CommentEditRequest,
    CommentResponse,
    comment_view,
)
from gpa.services import discussion as discussion_service

router = APIRouter(prefix="/api/v1/groups", tags=["discussion"])


def _thread_of(db: Session, comment) -> Thread:
    return db.get(Thread, comment.thread_id)


@router.get(
    "/{group_id}/events/{event_id}/comments", response_model=list[CommentResponse]
)
def list_comments(
    event_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """The event's discussion. Members see live comments only;
    organisers see the hidden and the tombstones too, flagged."""
    rows = discussion_service.list_comments(
        db, group=context.group, event_id=event_id, viewer_role=context.role
    )
    return [comment_view(row, _thread_of(db, row)) for row in rows]


@router.post(
    "/{group_id}/events/{event_id}/comments",
    response_model=CommentResponse,
    status_code=201,
)
def post_comment(
    event_id: str,
    body: CommentCreateRequest,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Post to the event's thread, as yourself — a seat's words
    are the seat's (B-018), a person's are theirs."""
    comment = discussion_service.post_comment(
        db,
        author_label=principal.label,
        author_user_id=principal.user_id,
        author_seat_id=principal.seat_id,
        group=context.group,
        event_id=event_id,
        viewer_role=context.role,
        body=body.body,
    )
    return comment_view(comment, _thread_of(db, comment))


@router.patch("/{group_id}/comments/{comment_id}", response_model=CommentResponse)
def edit_comment(
    comment_id: str,
    body: CommentEditRequest,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Edit your own comment (nobody else's — ever)."""
    comment = discussion_service.edit_comment(
        db,
        author_label=principal.label,
        user_id=principal.user_id,
        seat_id=principal.seat_id,
        group=context.group,
        comment_id=comment_id,
        body=body.body,
    )
    return comment_view(comment, _thread_of(db, comment))


@router.delete("/{group_id}/comments/{comment_id}", response_model=CommentResponse)
def delete_comment(
    comment_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Delete your own comment: a tombstone, returned flagged."""
    comment = discussion_service.delete_comment(
        db,
        author_label=principal.label,
        user_id=principal.user_id,
        seat_id=principal.seat_id,
        group=context.group,
        comment_id=comment_id,
    )
    return comment_view(comment, _thread_of(db, comment))


@router.post(
    "/{group_id}/comments/{comment_id}/hide", response_model=CommentResponse
)
def hide_comment(
    comment_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Moderation: hide a comment (audited, reversible)."""
    comment = discussion_service.set_hidden(
        db, actor_label=principal.label, group=context.group,
        comment_id=comment_id, hidden=True,
    )
    return comment_view(comment, _thread_of(db, comment))


@router.post(
    "/{group_id}/comments/{comment_id}/unhide", response_model=CommentResponse
)
def unhide_comment(
    comment_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Moderation, reversed: the comment returns to view."""
    comment = discussion_service.set_hidden(
        db, actor_label=principal.label, group=context.group,
        comment_id=comment_id, hidden=False,
    )
    return comment_view(comment, _thread_of(db, comment))
