"""The group event stream (roadmap B-033, §5's stream contract).

What this file is for: a group's screens — the frontend's review
queue, the terminal app later — need to watch ingest WORK happen:
a transcription queued, running, done. This module is that watch.

It is deliberately built on the Job table, the durable record,
and NOT on an in-memory event bus: a bus forgets everything the
moment the server restarts or a second process serves, while the
table is the same truth the retry machinery and the Doctor read.
The generator polls the group's jobs and speaks two event kinds:

- ``snapshot`` — once, on connect: the group's recent jobs with
  their status and progress, so a fresh screen paints the world
  as it is;
- ``job.progress`` — whenever a job's status or progress
  changes: id, kind, status, progress, and the source it serves.

Honesty note (B-033): the ingests that complete synchronously
(paste, file, newsletter, image, link) never pass through a job,
so their stage/progress arrives final in the create response —
there is nothing to stream. Job-driven work (transcription
today, extraction and publishing later) is what flows here.
"""

import json
import time
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from gpa.models.core import Job

# How much of a group's job history a snapshot carries. Screens
# care about recent work; the full history lives behind the jobs
# API and the audit trail.
SNAPSHOT_LIMIT = 50


def _payload(job: Job) -> dict:
    try:
        return json.loads(job.payload_json or "{}")
    except json.JSONDecodeError:
        return {}


def _job_summary(job: Job) -> dict:
    payload = _payload(job)
    return {
        "job_id": job.id,
        "kind": job.kind,
        "status": job.status,
        "progress": job.progress,
        "source_id": payload.get("source_id"),
    }


def group_jobs(db: Session, group_id: str) -> list[Job]:
    """The group's jobs, newest first (jobs name their group in
    their payload — the chassis' one addressing rule)."""
    rows = (
        db.query(Job)
        .order_by(Job.created_at.desc(), Job.id.desc())
        .limit(500)
        .all()
    )
    return [job for job in rows if _payload(job).get("group_id") == group_id]


def snapshot(db: Session, group_id: str) -> dict:
    """The connect-time picture: recent jobs with status/progress."""
    jobs = group_jobs(db, group_id)[:SNAPSHOT_LIMIT]
    return {"group_id": group_id, "jobs": [_job_summary(job) for job in jobs]}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def group_events(
    session_factory: Callable[[], Session],
    group_id: str,
    *,
    poll_seconds: float = 1.0,
    max_polls: int | None = None,
) -> Iterator[str]:
    """Yield SSE frames: one snapshot, then job.progress changes.

    ``max_polls`` bounds the generator for tests and short-lived
    consumers; the HTTP route leaves it None and the stream runs
    until the client disconnects. Each poll reads through a
    fresh session — the table, not this process's memory, is
    the state being watched.
    """
    seen: dict[str, tuple[str, int]] = {}
    with session_factory() as db:
        snap = snapshot(db, group_id)
    for job in snap["jobs"]:
        seen[job["job_id"]] = (job["status"], job["progress"])
    yield _sse("snapshot", snap)
    polls = 0
    while max_polls is None or polls < max_polls:
        time.sleep(poll_seconds)
        polls += 1
        with session_factory() as db:
            jobs = group_jobs(db, group_id)[:SNAPSHOT_LIMIT]
        for job in jobs:
            summary = _job_summary(job)
            state = (summary["status"], summary["progress"])
            if seen.get(summary["job_id"]) != state:
                seen[summary["job_id"]] = state
                yield _sse("job.progress", summary)
