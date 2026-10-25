"""Nonprofit-pack schemas (roadmap Phase 9).

The wire shapes for sub-groups, announcements, shifts,
resources, attendance, member import/export, and the group
settings pack. As everywhere here: response shapes are built
from the rows by small view functions beside them, and request
shapes validate the closed vocabularies before a service runs.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ------------------------------------------------------------------
# Sub-groups (B-105)
# ------------------------------------------------------------------


class SubGroupCreateRequest(BaseModel):
    """Open a named sub-group (a chapter, a crew) in a group."""

    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class SubGroupPatchRequest(BaseModel):
    """Rename / re-describe a sub-group; only sent fields change."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class SubGroupResponse(BaseModel):
    """One sub-group, with its enrolled headcount."""

    id: str
    group_id: str
    name: str
    description: str = ""
    member_count: int = 0
    created_by: str
    created_at: str


class SubGroupEnrollRequest(BaseModel):
    """Enrol one group member; ``role`` is the optional
    per-sub-group role override (an organiser's grant)."""

    user_id: str
    role: str | None = None


class SubGroupMemberResponse(BaseModel):
    """One enrolled member: their group role, their per-sub-group
    role when one was granted, and the effective role."""

    user_id: str
    name: str = ""
    email: str = ""
    group_role: str | None = None
    subgroup_role: str | None = None
    effective_role: str | None = None


# ------------------------------------------------------------------
# Announcements (B-106)
# ------------------------------------------------------------------


class AnnouncementCreateRequest(BaseModel):
    """Post to the board. Times arrive as ISO-8601; the router
    converts them to stored UTC before the service runs."""

    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1)
    pinned: bool = False
    expires_at: datetime | None = None
    subgroup_id: str | None = None


class AnnouncementPatchRequest(BaseModel):
    """Edit a post; only sent fields change. An explicit
    ``expires_at: null`` un-expires the post."""

    title: str | None = Field(default=None, min_length=1, max_length=240)
    body: str | None = Field(default=None, min_length=1)
    pinned: bool | None = None
    expires_at: datetime | None = None
    subgroup_id: str | None = None


class AnnouncementResponse(BaseModel):
    """One board post. ``expired`` is computed at read time —
    expiry is a state the row grows into, never a deletion."""

    id: str
    group_id: str
    subgroup_id: str | None = None
    title: str
    body: str
    pinned: bool = False
    expires_at: str | None = None
    expired: bool = False
    created_by: str
    created_at: str
    updated_at: str


def announcement_view(row, *, expired: bool = False) -> AnnouncementResponse:
    """Build one announcement's response from its row."""
    return AnnouncementResponse(
        id=row.id,
        group_id=row.group_id,
        subgroup_id=row.subgroup_id,
        title=row.title,
        body=row.body,
        pinned=row.pinned,
        expires_at=row.expires_at.isoformat() + "Z" if row.expires_at else None,
        expired=expired,
        created_by=row.created_by,
        created_at=row.created_at.isoformat() + "Z",
        updated_at=row.updated_at.isoformat() + "Z",
    )


def subgroup_view(subgroup, member_count: int = 0) -> SubGroupResponse:
    """Build one sub-group's response from its row (the router
    supplies the enrolled headcount — views never query)."""
    return SubGroupResponse(
        id=subgroup.id,
        group_id=subgroup.group_id,
        name=subgroup.name,
        description=subgroup.description,
        member_count=member_count,
        created_by=subgroup.created_by,
        created_at=subgroup.created_at.isoformat() + "Z",
    )
