"""Group memory (roadmap Phase 10, B-113 → B-122; Doc 04 §12).

The service layer over Geoffrey's pruning engine
(``gpa.ai.pruning``). What lives here:

- **The corpus** — the group's *approved history*, and nothing
  else: source chunks (material a member brought in under a
  permission record), the group's CURRENT decisions (settled
  truth), and summaries a person approved into the memory.
  Pending drafts and rejected candidates are **not** the group's
  past and never enter the corpus — an answer may only ever
  cite what the group actually said or settled.
- **Runs** — every engine run is written down (``PruneRun``:
  input, kept, dropped, passes, model, cost) and every model
  call is ledgered (``AiUsage``, B-047) inside the same
  transaction, committed before any answer is given.
- **The doors built on the engine** — ask (B-115), discussion
  summaries (B-116), briefings (B-117), recaps and the
  newsletter loop (B-118) — each its own function below, each
  storing a ``Summary`` with its source range, so nothing the
  engine says is ever unsourced (B-120).

The engine itself stays pure (ai/pruning.py); the honesty rules
live here and in the prompts: citations are verified against
the kept chunks before an answer is returned, drafts go to the
review queue or sit as draft summaries — the engine never
writes a decision, a task, or a sent message.
"""

import json

from sqlalchemy.orm import Session

from gpa.ai import client as ai_client
from gpa.ai import pruning
from gpa.ai.client import estimate_tokens
from gpa.config import Settings, get_settings
from gpa.models.groups import Group
from gpa.models.memory import PruneRun, Summary
from gpa.models.planning import Decision
from gpa.models.sources import Source
from gpa.services import audit
from gpa.services import sources as source_service
from gpa.services import usage as usage_service

# Machine authors, in the extraction service's vocabulary: a
# machine's words are never attributed to a person.
ASK_AUTHOR = "system:memory"


def approved_corpus(db: Session, group: Group) -> list[pruning.MemoryChunk]:
    """The group's approved history as ordered memory chunks.

    Order is the corpus's own chronology: each chunk's moment
    (a message's sent-at, a decision's making, a summary's
    approval-era creation), ties broken by build order; the
    positions are then assigned 0..N-1 in that order, so a
    citation's position is stable for the whole run.
    """
    staged: list[tuple[object, pruning.MemoryChunk]] = []

    sources = (
        db.query(Source)
        .filter(Source.group_id == group.id)
        .order_by(Source.created_at, Source.id)
        .all()
    )
    for source in sources:
        for chunk in source_service.list_chunks(db, source):
            staged.append(
                (
                    chunk.sent_at or source.created_at,
                    pruning.MemoryChunk(
                        chunk_id=chunk.id,
                        position=0,  # assigned after the sort
                        text=chunk.text,
                        sender=chunk.sender,
                        sent_at=chunk.sent_at,
                        origin="source",
                    ),
                )
            )

    # Settled truth weighs first-class: a CURRENT decision is
    # the group's past in its most distilled form. Superseded
    # decisions are history ABOUT the truth, not the truth —
    # they stay out (the source that superseded them speaks).
    decisions = (
        db.query(Decision)
        .filter(Decision.group_id == group.id, Decision.status == "current")
        .order_by(Decision.created_at, Decision.id)
        .all()
    )
    for decision in decisions:
        staged.append(
            (
                decision.created_at,
                pruning.MemoryChunk(
                    chunk_id=f"decision:{decision.id}",
                    position=0,
                    text=decision.text,
                    sender="the group (decision)",
                    sent_at=decision.created_at,
                    origin="decision",
                ),
            )
        )

    # Summaries a person APPROVED into the memory — the group's
    # own digested past (a recap of last year's fair is exactly
    # what this year's briefing should find). Drafts are not
    # memory yet; ask answers are answers, not history.
    approved = (
        db.query(Summary)
        .filter(
            Summary.group_id == group.id,
            Summary.status == "approved",
            Summary.kind.in_(("discussion", "recap")),
        )
        .order_by(Summary.created_at, Summary.id)
        .all()
    )
    for summary in approved:
        staged.append(
            (
                summary.created_at,
                pruning.MemoryChunk(
                    chunk_id=f"summary:{summary.id}",
                    position=0,
                    text=summary.body,
                    sender="the group (approved summary)",
                    sent_at=summary.created_at,
                    origin="summary",
                ),
            )
        )

    staged.sort(key=lambda pair: (pair[0] is None, pair[0]))
    corpus: list[pruning.MemoryChunk] = []
    for position, (_moment, chunk) in enumerate(staged):
        chunk.position = position
        corpus.append(chunk)
    return corpus


def resolve_client(settings: Settings | None, group: Group):
    """The engine's judge for this group (B-119 grows the local
    road here): by default the process's configured driver —
    swapping drivers stays a configuration choice, never a code
    change (B-035)."""
    return ai_client.get_client()


def _record_usage(db: Session, group: Group):
    """The engine's usage callback: ledger each call in the
    caller's transaction (B-047), stamped with its prompt."""

    def record(result, prompt_name):
        usage_service.record_usage(
            db, result=result, group_id=group.id,
            operation=f"prune:{prompt_name}", prompt_name=prompt_name,
            prompt_version=None,
        )

    return record


def write_prune_run(
    db: Session,
    *,
    actor_label: str,
    group: Group,
    question: str,
    purpose: str,
    corpus: list[pruning.MemoryChunk],
    outcome: pruning.PruneOutcome,
) -> PruneRun:
    """Persist one run's account (B-113). NO commit — the
    caller's transaction owns it, so a run record can never
    outlive the answer it accounted for (nor the reverse)."""
    row = PruneRun(
        group_id=group.id,
        purpose=purpose,
        question=question,
        input_chunks=len(corpus),
        input_tokens=sum(estimate_tokens(c.text) for c in corpus),
        kept_json=json.dumps([c.chunk_id for c in outcome.kept]),
        dropped_json=json.dumps([c.chunk_id for c in outcome.dropped]),
        passes=outcome.passes,
        model_id=outcome.model_id,
        cost_micros=outcome.cost_micros,
        created_by=actor_label,
    )
    db.add(row)
    db.flush()  # the id exists before a summary's range names it
    return row


def run_prune(
    db: Session,
    settings: Settings | None = None,
    *,
    actor_label: str,
    group: Group,
    question: str,
    purpose: str = "prune",
    corpus: list[pruning.MemoryChunk] | None = None,
    client=None,
    max_passes: int | None = None,
    token_budget: int | None = None,
) -> tuple[PruneRun, pruning.PruneOutcome, list[pruning.MemoryChunk]]:
    """Run the engine over the group's corpus and write the
    run down. Commits before returning (commit-before-answer:
    the record exists before anyone acts on the outcome).

    Pass cap and budget default to the group's settings-pack
    dials (B-114); the engine enforces its own harder ceiling
    whatever it is handed.
    """
    settings = settings or get_settings()
    corpus = corpus if corpus is not None else approved_corpus(db, group)
    client = client if client is not None else resolve_client(settings, group)
    outcome = pruning.prune_multi(
        client,
        question=question,
        chunks=corpus,
        max_passes=group.prune_max_passes if max_passes is None else max_passes,
        token_budget=group.prune_token_budget if token_budget is None else token_budget,
        record_usage=_record_usage(db, group),
    )
    row = write_prune_run(
        db, actor_label=actor_label, group=group, question=question,
        purpose=purpose, corpus=corpus, outcome=outcome,
    )
    audit.record(
        db, actor=actor_label, action="memory.prune_run",
        group_id=group.id, entity_type="prune_run", entity_id=row.id,
        detail={
            "purpose": purpose,
            "input_chunks": row.input_chunks,
            "kept": len(outcome.kept),
            "dropped": len(outcome.dropped),
            "passes": outcome.passes,
            "budget_stopped": outcome.budget_stopped,
        },
    )
    db.commit()
    return row, outcome, corpus
