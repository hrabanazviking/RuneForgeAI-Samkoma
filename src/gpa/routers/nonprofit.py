"""Nonprofit-pack routers (roadmap Phase 9).

Sub-groups, the announcements board, volunteer shifts,
resources, attendance, member import/export, and the group
settings pack. Every route takes its caller from deps.py — the
one door (B-017) — and the permission each route needs is named
in its dependency, never hand-rolled in the handler.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gpa.db import get_db
from gpa.deps import GroupContext, Principal, require_group_role, require_scope
from gpa.schemas.nonprofit import (
    SubGroupCreateRequest,
    SubGroupEnrollRequest,
    SubGroupMemberResponse,
    SubGroupPatchRequest,
    SubGroupResponse,
    subgroup_view,
)
from gpa.services import subgroups as subgroup_service

subgroups_router = APIRouter(prefix="/api/v1/groups", tags=["subgroups"])


@subgroups_router.post(
    "/{group_id}/subgroups", response_model=SubGroupResponse, status_code=201
)
def create_subgroup(
    body: SubGroupCreateRequest,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Open a named sub-group (organiser+)."""
    subgroup = subgroup_service.create_subgroup(
        db, actor_label=principal.label, group=context.group,
        name=body.name, description=body.description,
    )
    return subgroup_view(subgroup, subgroup_service.member_count(db, subgroup))


@subgroups_router.get("/{group_id}/subgroups", response_model=list[SubGroupResponse])
def list_subgroups(
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """The group's sub-groups, name order, with headcounts."""
    return [
        subgroup_view(row, subgroup_service.member_count(db, row))
        for row in subgroup_service.list_subgroups(db, context.group)
    ]


@subgroups_router.get(
    "/{group_id}/subgroups/{subgroup_id}", response_model=SubGroupResponse
)
def read_subgroup(
    subgroup_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """One sub-group."""
    subgroup = subgroup_service.get_subgroup(db, context.group, subgroup_id)
    return subgroup_view(subgroup, subgroup_service.member_count(db, subgroup))


@subgroups_router.patch(
    "/{group_id}/subgroups/{subgroup_id}", response_model=SubGroupResponse
)
def update_subgroup(
    subgroup_id: str,
    body: SubGroupPatchRequest,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Rename / re-describe a sub-group (organiser+)."""
    subgroup = subgroup_service.update_subgroup(
        db, actor_label=principal.label, group=context.group,
        subgroup_id=subgroup_id, changes=body.model_dump(exclude_unset=True),
    )
    return subgroup_view(subgroup, subgroup_service.member_count(db, subgroup))


@subgroups_router.delete("/{group_id}/subgroups/{subgroup_id}", status_code=204)
def delete_subgroup(
    subgroup_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("publish")),
    db: Session = Depends(get_db),
):
    """Remove a sub-group (organiser+). Refused while content is
    still scoped to it — a delete must never widen an audience."""
    subgroup_service.delete_subgroup(
        db, actor_label=principal.label, group=context.group,
        subgroup_id=subgroup_id,
    )


@subgroups_router.post(
    "/{group_id}/subgroups/{subgroup_id}/members",
    response_model=SubGroupMemberResponse,
    status_code=201,
)
def enroll_member(
    subgroup_id: str,
    body: SubGroupEnrollRequest,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Enrol a group member in a sub-group. Organisers enrol
    anyone; a member may enrol THEMSELVES (the service holds
    that rule, so no route can forget it)."""
    subgroup_service.enroll_member(
        db, actor_label=principal.label, actor_user_id=principal.user_id,
        actor_role=context.role, group=context.group,
        subgroup_id=subgroup_id, user_id=body.user_id, role=body.role,
    )
    subgroup = subgroup_service.get_subgroup(db, context.group, subgroup_id)
    for member in subgroup_service.list_members(db, context.group, subgroup):
        if member["user_id"] == body.user_id:
            return SubGroupMemberResponse(**member)
    raise AssertionError("enrolled member missing from the member list")


@subgroups_router.get(
    "/{group_id}/subgroups/{subgroup_id}/members",
    response_model=list[SubGroupMemberResponse],
)
def list_subgroup_members(
    subgroup_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """Who is enrolled, with group / per-sub-group / effective roles."""
    subgroup = subgroup_service.get_subgroup(db, context.group, subgroup_id)
    return [
        SubGroupMemberResponse(**member)
        for member in subgroup_service.list_members(db, context.group, subgroup)
    ]


@subgroups_router.delete(
    "/{group_id}/subgroups/{subgroup_id}/members/{user_id}", status_code=204
)
def unenroll_member(
    subgroup_id: str,
    user_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Remove an enrolment (organiser, or the person themselves)."""
    subgroup_service.unenroll_member(
        db, actor_label=principal.label, actor_user_id=principal.user_id,
        actor_role=context.role, group=context.group,
        subgroup_id=subgroup_id, user_id=user_id,
    )
