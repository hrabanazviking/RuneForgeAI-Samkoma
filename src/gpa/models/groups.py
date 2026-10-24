"""Group tables (roadmap B-015 → B-018).

A group is the home of one community's planning. Who belongs, with
which role, is a Membership row; an AI participant belongs through
an AgentSeat row of its own — a seat is a first-class member with a
role, never a fake user (roadmap D-35).
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from gpa.db import Base
from gpa.models.identity import new_id, now_utc

# The role ladder, least to most power. Permission checks compare by
# position in this tuple, never by scattered string comparisons.
ROLE_ORDER: tuple[str, ...] = ("guest", "member", "organiser", "admin", "owner")

# Group visibility (B-015). Private groups must not leak their
# existence: a non-member asking gets a 404, not a 403.
VISIBILITIES: tuple[str, ...] = ("private", "invite", "public-listed")


def role_at_least(role: str, minimum: str) -> bool:
    """True when ``role`` is at or above ``minimum`` on the ladder."""
    return ROLE_ORDER.index(role) >= ROLE_ORDER.index(minimum)


class Group(Base):
    """One community's planning home."""

    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160))
    # URL-friendly unique name; collisions get a numeric suffix
    # (services/groups.py owns that rule).
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    home_timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    default_place: Mapped[str] = mapped_column(String(240), default="")
    # The per-group daily AI budget (Phase 3, B-047), in integer
    # micro-units of currency to match the AiUsage ledger. NULL
    # means "no cap set" — the soft-stop has nothing to stop at.
    ai_daily_budget_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Membership(Base):
    """A user's place in a group: their role and invite state."""

    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="member")
    # invited -> active (accepted) | declined. Only active counts.
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class AgentSeat(Base):
    """An AI participant's seat in one group (B-018).

    A seat has a display name, a role on the same ladder, and (via
    its ApiKey) scopes. Everything a seat does is audited as the
    seat — never as the human who created it.
    """

    __tablename__ = "agent_seats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(16), default="member")
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Candidate(Base):
    """A draft awaiting the review queue (B-018 stub, grown by
    Phase 3 into the full candidate of roadmap §4).

    A candidate is the ONLY thing AI pipelines may create: fields
    drafted from a source, each with its confidence and (through
    ``Provenance`` rows) the exact quote that supports it. A person
    approves, edits, rejects, or merges it; approval is the only
    path from draft to published entity (Phase 4 mints the entity
    and fills ``resulting_entity_*`` — until then the link stays
    empty, honestly).
    """

    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32), default="event")
    title: Mapped[str] = mapped_column(String(240), default="")
    # Who drafted it, as an audit-friendly label: "user:<id>" or
    # "seat:<id>" — a seat's work is never attributed to its owner.
    # Machine-drafted candidates say "system:extraction"; the
    # person who requested the run is on the job + audit rows.
    created_by: Mapped[str] = mapped_column(String(80))
    # pending | edited -> approved | rejected | merged; a re-run's
    # fresh drafts mark the old undecided ones superseded (B-045).
    status: Mapped[str] = mapped_column(String(16), default="pending")
    approved_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # The draft itself, as JSON (B-040): the kind's fields at top
    # level (title / starts_at / place …) plus a "fields" map —
    # per field: value, confidence, quote, supported — so the
    # queue can show exactly what the model claimed and what the
    # source actually backs. Plain text column; services own the
    # shape (ai/extraction.py writes it, services/quality.py reads
    # it for flags).
    draft_json: Mapped[str] = mapped_column(Text, default="{}")
    # Candidate-level confidence: the mean of its supported fields'
    # confidences (per-field numbers live in the draft; this is the
    # queue's sort/filter number, B-043). NULL for hand-made stubs.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Server-computed quality flags (B-044), a JSON list of closed
    # vocabulary strings the frontend renders verbatim.
    flags_json: Mapped[str] = mapped_column(Text, default="[]")
    # Which prompt (name + version) produced this draft (B-038) —
    # a candidate can always answer "which instructions made you?"
    prompt_name: Mapped[str] = mapped_column(String(64), default="")
    prompt_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The extraction job that produced this draft (B-045); plain
    # string, like the audit's entity references.
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # When this candidate was merged into another (B-043): the
    # survivor's id. The merged row keeps its draft + provenance —
    # merging decides, it does not erase.
    merged_into_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # The published entity approval minted (Phase 4, B-049). Until
    # Phase 4 exists these stay NULL on purpose: approval records
    # the DECISION here; minting is the events module's job, and a
    # filled link before then would be a lie in the database.
    resulting_entity_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resulting_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_utc, onupdate=now_utc
    )
    # The source this draft was drawn from (Phase 2, B-023). A
    # PLAIN STRING, not a foreign key, on purpose: deleting a
    # source must never cascade-delete an approved candidate — the
    # id stays as a tombstone and ``source_deleted_at`` says when
    # the material behind it went away. The candidate keeps its
    # text; it loses its quotes (see models/sources.py Provenance).
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
