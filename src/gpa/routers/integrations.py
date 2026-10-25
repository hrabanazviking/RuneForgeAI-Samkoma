"""Integration routes (roadmap Phase 11, B-123 → B-128).

The doors onto the bridge: account links and live sync
(B-123), the Samtal calendar return path (B-124), the
integration framework (B-127), the inbound webhook endpoints
(B-126), and outbound webhooks with their deliveries
(B-128). Every handler authorises through gpa.deps like
every other router and defers every rule to the services —
routers here shape responses and nothing more.

The webhook RECEIVER is the one unauthenticated door in this
file, by design and by precedent (B-030's email-in): its
credential is the token in its path plus the HMAC signature
on its body, verified inside services/webhooks_in.py before
a single chunk is written.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from gpa.db import get_db
from gpa.deps import GroupContext, Principal, require_group_role, require_scope
from gpa.models.identity import User
from gpa.schemas.integrations import (
    AccountLinkCreateRequest,
    AccountLinkResponse,
    LiveSyncResponse,
    SpeakerMember,
    SpeakerResponse,
)
from gpa.services import livechat as livechat_service
from gpa.services import sources as source_service

router = APIRouter(prefix="/api/v1/groups", tags=["integrations"])

# The token-carrying receiver door (B-126 mounts its route
# here): no group in its path, because the token IS the
# address — the same shape as B-030's email-in router.
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["integrations"])


def _link_response(db: Session, link) -> AccountLinkResponse:
    user = db.get(User, link.user_id)
    return AccountLinkResponse(
        id=link.id, group_id=link.group_id,
        connector_kind=link.connector_kind,
        external_user_id=link.external_user_id,
        external_name=link.external_name,
        user_id=link.user_id,
        member_name=user.name if user is not None else "",
        created_at=link.created_at.isoformat(),
    )


# --- Account links (B-123) ---------------------------------------------
# Identity administration is an organiser act: a link decides
# whose words belong to whom, and that is never a member's
# self-service claim.


@router.post(
    "/{group_id}/account-links",
    response_model=AccountLinkResponse,
    status_code=201,
)
def create_account_link(
    body: AccountLinkCreateRequest,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("admin")),
    db: Session = Depends(get_db),
):
    """Link one outside identity to one member of this group.

    The link keys on the outside id — the response shows the
    member it now resolves to. A name is never a key: nothing
    in this API can link by name."""
    link = livechat_service.create_link(
        db, actor_label=principal.label, group=context.group,
        connector_kind=body.connector_kind,
        external_user_id=body.external_user_id,
        external_name=body.external_name,
        user_id=body.user_id,
    )
    return _link_response(db, link)


@router.get(
    "/{group_id}/account-links", response_model=list[AccountLinkResponse]
)
def list_account_links(
    context: GroupContext = Depends(require_group_role("organiser")),
    db: Session = Depends(get_db),
):
    """Every account link in the group (organiser+)."""
    return [
        _link_response(db, link)
        for link in livechat_service.list_links(db, context.group)
    ]


@router.delete("/{group_id}/account-links/{link_id}", status_code=204)
def delete_account_link(
    link_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("admin")),
    db: Session = Depends(get_db),
):
    """Remove one link (organiser+). The speaker's chunks
    stay; they simply stop resolving to the member."""
    livechat_service.delete_link(
        db, actor_label=principal.label, group=context.group, link_id=link_id
    )
    return None


# --- Live sync + speakers (B-123) ---------------------------------------


@router.post(
    "/{group_id}/sources/{source_id}/sync", response_model=LiveSyncResponse
)
def sync_live_source(
    source_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Poll a live source's connector for new messages.

    New messages land as chunks, in order, under the
    permission record the source was registered with. A
    connector that cannot answer — no live Samtal configured,
    Messenger's ungranted access — refuses in plain words and
    the refusal is recorded on the source's sync state."""
    source = source_service.get_source(db, context.group, source_id)
    result = livechat_service.sync_live_source(
        db, actor_label=principal.label, group=context.group, source=source
    )
    return LiveSyncResponse(
        source_id=source.id, added=result["added"], cursor=result["cursor"],
        status=source.status, stage=source.stage,
    )


@router.get(
    "/{group_id}/sources/{source_id}/speakers",
    response_model=list[SpeakerResponse],
)
def list_speakers(
    source_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """A live source's speakers, resolved through account
    links (member+). Unlinked speakers answer guest=True —
    even when their name is a member's name. That is the
    identity law, and this response is where it shows."""
    source = source_service.get_source(db, context.group, source_id)
    return [
        SpeakerResponse(
            external_id=row["external_id"],
            name=row["name"],
            member=(
                SpeakerMember(**row["member"])
                if row["member"] is not None
                else None
            ),
            guest=row["guest"],
        )
        for row in livechat_service.speakers_of(db, context.group, source)
    ]
