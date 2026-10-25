"""Privacy routes (Phase 13): group export + erasure
(B-143) and the per-group permission listing (B-144).

Export and erasure are the OWNER's acts, and a person's —
never a seat's, never an API key's: the caller must be the
group's owner, signed in with a live session (a key, however
widely scoped, is a delegated credential, and delegating
ERASURE was never on the table).
"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from gpa.deps import GroupContext, Principal, get_db, get_principal, require_group_role
from gpa.errors import AppError
from gpa.schemas.privacy import EraseRequest, EraseResponse
from gpa.services import erasure as erasure_service

router = APIRouter(prefix="/api/v1/groups", tags=["privacy"])


def require_owner_person(
    context: GroupContext = Depends(require_group_role("owner")),
    principal: Principal = Depends(get_principal),
) -> GroupContext:
    """Owner role (the group door) PLUS a live person session:
    seats hold no owner role and are refused by the door;
    this guard adds the API-key refusal."""
    if principal.kind != "user" or principal.key_id is not None:
        raise AppError(
            "forbidden",
            detail=(
                "This needs the group's owner, signed in — "
                "an API key cannot export or erase a group."
            ),
        )
    return context


@router.post("/{group_id}/export")
def export_group(
    group_id: str,
    request: Request,
    context: GroupContext = Depends(require_owner_person),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """Download the group's whole archive (B-143): JSON by
    domain, the calendar as iCal, the stored files as
    themselves — one ZIP a human can open."""
    data, filename = erasure_service.build_export(
        db,
        settings=request.app.state.settings,
        storage=request.app.state.storage,
        group=context.group,
        actor_label=principal.label,
    )
    db.commit()  # the export's audit row lands before answering
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{group_id}/erase", response_model=EraseResponse)
def erase_group_route(
    group_id: str,
    body: EraseRequest,
    request: Request,
    context: GroupContext = Depends(require_owner_person),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """Hard-erase the group (B-143). Double confirmation: the
    group's exact name typed back, and the word ERASE. A
    mismatch refuses with the group untouched."""
    if body.confirm_name != context.group.name or body.confirm_word != "ERASE":
        raise AppError(
            "validation_error",
            detail=(
                "To erase this group, type its exact name and "
                "the word ERASE. Nothing was erased."
            ),
        )
    return erasure_service.erase_group(
        db,
        database=request.app.state.db,
        storage=request.app.state.storage,
        group=context.group,
        actor_label=principal.label,
    )
