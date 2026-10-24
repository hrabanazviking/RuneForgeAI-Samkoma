"""Group schemas: groups, memberships, seats, candidates (Phase 1)."""

from pydantic import BaseModel, Field


class GroupCreateRequest(BaseModel):
    """Create a group; the creator becomes its owner (B-015)."""

    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    visibility: str = Field(default="private")
    home_timezone: str = Field(default="UTC", max_length=64)
    default_place: str = Field(default="", max_length=240)


class GroupUpdateRequest(BaseModel):
    """Edit a group's settings (admin+; B-015)."""

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    visibility: str | None = None
    home_timezone: str | None = Field(default=None, max_length=64)
    default_place: str | None = Field(default=None, max_length=240)


class GroupResponse(BaseModel):
    """A group as the API shows it."""

    id: str
    name: str
    slug: str
    description: str
    visibility: str
    home_timezone: str
    default_place: str
    my_role: str | None = None


class InviteRequest(BaseModel):
    """Invite a person by email with a starting role (B-016)."""

    email: str = Field(min_length=3, max_length=320)
    role: str = Field(default="member")


class RoleChangeRequest(BaseModel):
    """Change a member's role (B-016)."""

    role: str


class MembershipResponse(BaseModel):
    """One membership row: who, with which role, in which state."""

    id: str
    user_id: str
    email: str
    name: str
    role: str
    status: str


class SeatCreateRequest(BaseModel):
    """Create an agent seat (B-018): a name, a role, and the scopes
    its key will carry. Approval is never among a seat's powers."""

    name: str = Field(min_length=1, max_length=120)
    role: str = Field(default="member")
    scopes: list[str] = Field(default_factory=lambda: ["read", "draft"])


class SeatResponse(BaseModel):
    """A seat as listed. ``key`` appears only at creation."""

    id: str
    group_id: str
    name: str
    role: str
    key: str | None = None
    key_prefix: str | None = None


class CandidateCreateRequest(BaseModel):
    """Draft a candidate for the review queue (stub, B-018)."""

    kind: str = Field(default="event", max_length=32)
    title: str = Field(min_length=1, max_length=240)


class CandidateResponse(BaseModel):
    """A candidate as the queue shows it."""

    id: str
    group_id: str
    kind: str
    title: str
    status: str
    created_by: str
    approved_by: str | None = None
