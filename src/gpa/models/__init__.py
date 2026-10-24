"""SQLAlchemy models, one module per domain.

Importing this package registers every table on ``Base.metadata`` —
Alembic and the test fixtures both rely on that. Domain files:

    identity.py  users, one-time tokens, refresh tokens, API keys
    groups.py    groups, memberships, agent seats, candidate stub
    core.py      jobs, the append-only audit log, file assets
    sources.py   sources, ordered chunks, provenance, flyers,
                 inbound email addresses
"""

from gpa.models.core import AuditLog, FileAsset, Job
from gpa.models.groups import AgentSeat, Candidate, Group, Membership
from gpa.models.identity import ApiKey, OneTimeToken, RefreshToken, User
from gpa.models.sources import Flyer, InboundAddress, Provenance, Source, SourceChunk

__all__ = [
    "ApiKey",
    "AgentSeat",
    "AuditLog",
    "Candidate",
    "FileAsset",
    "Flyer",
    "Group",
    "InboundAddress",
    "Job",
    "Membership",
    "OneTimeToken",
    "Provenance",
    "RefreshToken",
    "Source",
    "SourceChunk",
    "User",
]
