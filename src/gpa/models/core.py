"""Core tables shared by every domain (roadmap B-007/B-008/B-019).

Jobs (the durable background-work queue), the append-only audit log,
and file assets (the record of what the storage layer holds).
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gpa.db import Base
from gpa.models.identity import new_id, now_utc


class Job(Base):
    """One unit of background work (B-008).

    A job is a ROW before it is work: enqueue commits the row, the
    worker claims it with an update (so two workers can never run
    the same job), failures retry with exponential backoff, and
    after ``max_attempts`` the job is dead-lettered — visible, never
    silently dropped.
    """

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    last_error: Mapped[str] = mapped_column(Text, default="")
    locked_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class AuditLog(Base):
    """Append-only audit record (B-019).

    Rows describe an action by an actor (a user or a seat) on an
    entity, with a JSON detail payload. Rows are never updated or
    deleted by application code — they must survive deletion of the
    entity they describe, so entity references are plain strings,
    not foreign keys.
    """

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(80))  # "user:<id>" | "seat:<id>"
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(48), default="")
    entity_id: Mapped[str] = mapped_column(String(36), default="")
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class FileAsset(Base):
    """A file held by the storage layer (B-007).

    The bytes live under a content-addressed key; this row is the
    human-facing record (name, type, size) that points at them.
    """

    __tablename__ = "file_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(96), index=True)
    filename: Mapped[str] = mapped_column(String(240), default="")
    mime: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
