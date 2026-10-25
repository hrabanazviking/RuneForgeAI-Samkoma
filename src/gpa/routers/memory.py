"""Memory routes (roadmap Phase 10, B-115 → B-120).

The doors onto the group's memory: ask it a question, list
what the engine has said (summaries), and inspect or purge the
prune runs behind the answers. Every handler authorises
through gpa.deps like every other router, and defers every
rule to services/memory.py.

Role doors, chosen once and kept: asking is a MEMBER act (the
memory is the group's own past, and a seat may ask it too —
Doc 04 §12); making the engine work (summarise, brief, recap,
draft a newsletter, approve a draft, purge runs) is ORGANISER
work, like requesting extraction — it spends the group's money
and shapes what the group remembers.
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gpa.db import get_db
from gpa.deps import GroupContext, require_group_role
from gpa.models.memory import PruneRun, Summary
from gpa.schemas.memory import (
    AskRequest,
    AskResponse,
    BriefingResponse,
    CitationResponse,
    PruneRunResponse,
    SummariseRequest,
    SummariseResponse,
    SummaryResponse,
)
from gpa.services import events as event_service
from gpa.services import memory as memory_service

router = APIRouter(prefix="/api/v1/groups", tags=["memory"])


def _summary_response(summary: Summary) -> SummaryResponse:
    try:
        citations = json.loads(summary.citations_json or "[]")
    except json.JSONDecodeError:
        citations = []
    try:
        source_range = json.loads(summary.range_json or "{}")
    except json.JSONDecodeError:
        source_range = {}
    return SummaryResponse(
        id=summary.id,
        group_id=summary.group_id,
        kind=summary.kind,
        title=summary.title,
        body=summary.body,
        status=summary.status,
        verified=summary.verified,
        question=summary.question,
        citations=[CitationResponse(**c) for c in citations],
        source_range=source_range if isinstance(source_range, dict) else {},
        event_id=summary.event_id,
        created_by=summary.created_by,
        created_at=summary.created_at,
    )


def _run_response(run: PruneRun) -> PruneRunResponse:
    def _ids(raw: str) -> list[str]:
        try:
            value = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []
        return [str(v) for v in value] if isinstance(value, list) else []

    return PruneRunResponse(
        id=run.id,
        group_id=run.group_id,
        purpose=run.purpose,
        question=run.question,
        input_chunks=run.input_chunks,
        input_tokens=run.input_tokens,
        kept_chunk_ids=_ids(run.kept_json),
        dropped_chunk_ids=_ids(run.dropped_json),
        passes=run.passes,
        model_id=run.model_id,
        cost_micros=run.cost_micros,
        created_by=run.created_by,
        created_at=run.created_at,
    )


# --- Ask (B-115) ---------------------------------------------------


@router.post("/{group_id}/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """Ask the group's approved history a question. The answer
    carries citations, or is the honest refusal — and either
    way it was committed (run + summary) before this answer
    was sent."""
    result = memory_service.ask_question(
        db, actor_label=context.principal.label, group=context.group,
        question=body.question,
    )
    return AskResponse(
        answer=result["answer"],
        verified=result["verified"],
        citations=[CitationResponse(**c) for c in result["citations"]],
        summary_id=result["summary_id"],
        prune_run_id=result["prune_run_id"],
    )


# --- Summaries: read + approve (B-116 → B-118 grow the writers) ----


@router.get("/{group_id}/summaries", response_model=list[SummaryResponse])
def list_summaries(
    kind: str | None = None,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """What the engine has said in this group, newest first —
    answers, briefings, and the drafts awaiting a person."""
    rows = memory_service.list_summaries(db, context.group, kind=kind)
    return [_summary_response(row) for row in rows]


@router.post(
    "/{group_id}/summaries/discussion",
    response_model=SummariseResponse, status_code=201,
)
def summarise_discussion(
    body: SummariseRequest,
    context: GroupContext = Depends(require_group_role("organiser")),
    db: Session = Depends(get_db),
):
    """Summarise a thread (B-116). The summary is stored as a
    draft; the decisions and next actions it names arrive as
    review-queue candidates — never as written decisions."""
    result = memory_service.summarise_thread(
        db, actor_label=context.principal.label, group=context.group,
        parent_type=body.parent_type, parent_id=body.parent_id,
        viewer_role=context.role,
    )
    return SummariseResponse(
        summary=_summary_response(result["summary"]),
        candidate_ids=[c.id for c in result["candidates"]],
    )


# --- Briefings (B-117) ----------------------------------------------


@router.post(
    "/{group_id}/events/{event_id}/briefing",
    response_model=BriefingResponse, status_code=201,
)
def brief_event(
    event_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """The host's briefing for one event: past decisions, last
    recap, open questions, role gaps — and the pruned history
    that matters, landmines included."""
    event = event_service.get_visible_event(
        db, context.group, event_id, context.role
    )
    result = memory_service.brief_event(
        db, actor_label=context.principal.label, group=context.group,
        event=event,
    )
    return BriefingResponse(
        summary=_summary_response(result["summary"]),
        open_questions=result["open_questions"],
        role_gaps=result["role_gaps"],
        prune_run_id=result["prune_run_id"],
    )
