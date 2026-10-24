"""Transcription job — the Phase 2 stub (roadmap B-031).

Voice notes arrive today; the transcription DRIVER (a real
speech-to-text model, behind the AI adapter) arrives in Phase 5.
Until then this handler is the honest placeholder the job queue
carries: it verifies the note and its stored audio are really
there, and completes — leaving the source exactly where its
status says it is, ``awaiting_transcription``. A job that
pretended to transcribe would be a lie told in the database; a
job that registers the note as waiting is the truth, and Phase 5
replaces this body without the queue, the source, or the API
changing shape.
"""

from sqlalchemy.orm import Session

from gpa.models.sources import Source
from gpa.services import jobs as job_service

JOB_KIND = "transcribe"


def handle_transcribe(db: Session, payload: dict) -> None:
    """Check one voice note is stored and awaiting its driver.

    A missing source or asset is a genuine failure (the job
    retries, then dead-letters, visibly). A present one needs
    nothing further until Phase 5 — the source's own status has
    said "awaiting transcription" since the moment it arrived.
    """
    source = db.get(Source, payload.get("source_id", ""))
    if source is None or source.kind != "voice":
        raise RuntimeError("transcribe job names no voice source")
    if not source.storage_key:
        raise RuntimeError("voice source has no stored audio")


def register_handlers() -> None:
    """Offer the transcribe handler to the job chassis (B-008)."""
    job_service.register_handler(JOB_KIND, handle_transcribe)


# Registration happens on import: any process that loads this
# module (the API via its router, the standalone worker) can run
# the job. Importing it twice is harmless — the registry is a dict.
register_handlers()
