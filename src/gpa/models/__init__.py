"""SQLAlchemy models, one module per domain.

Importing this package registers every table on ``Base.metadata`` —
Alembic and the test fixtures both rely on that. Domain files:

    identity.py  users, one-time tokens, refresh tokens, API keys
    groups.py    groups, memberships, agent seats, candidate stub
    core.py      jobs, the append-only audit log, file assets
    sources.py   sources, ordered chunks, provenance, flyers,
                 inbound email addresses
    ai.py        the AI usage ledger (Phase 3)
    events.py    events, their changes, recurrences, calendar
                 feeds, discussion threads/comments, RSVPs (Phase 4)
"""

from gpa.models.ai import AiUsage
from gpa.models.core import AuditLog, FileAsset, Job, Tombstone
from gpa.models.events import (
    AnnouncementDraft,
    CalendarFeed,
    Comment,
    Event,
    EventChange,
    EventContradiction,
    EventSourceLink,
    Recurrence,
    Rsvp,
    Thread,
)
from gpa.models.groups import AgentSeat, Candidate, Group, Membership
from gpa.models.identity import ApiKey, OneTimeToken, RefreshToken, User
from gpa.models.sources import Flyer, InboundAddress, Provenance, Source, SourceChunk

__all__ = [
    "AiUsage",
    "AnnouncementDraft",
    "ApiKey",
    "AgentSeat",
    "AuditLog",
    "CalendarFeed",
    "Candidate",
    "Comment",
    "Event",
    "EventChange",
    "EventContradiction",
    "EventSourceLink",
    "FileAsset",
    "Flyer",
    "Group",
    "InboundAddress",
    "Job",
    "Membership",
    "OneTimeToken",
    "Provenance",
    "Recurrence",
    "RefreshToken",
    "Rsvp",
    "Source",
    "SourceChunk",
    "Thread",
    "Tombstone",
    "User",
]
