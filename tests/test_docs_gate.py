"""B-181 documentation gate: index present, diagrams sound.

The acceptance B-181 names: a deliberately broken diagram fails
the gate, by file. These tests pin that against the real checker
(scripts/check_mermaid.py) — the same module test.sh invokes —
plus the standing law that every Mermaid diagram already in the
shipped documentation surface parses.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_mermaid", ROOT / "scripts" / "check_mermaid.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


def test_docs_index_orders_every_reader():
    """The B-181 index exists and orders readers user-first."""
    index = ROOT / "docs" / "README.md"
    assert index.exists()
    text = index.read_text(encoding="utf-8")
    # Reader order in section 6A.8: user -> admin -> frontend ->
    # backend -> operator surfaces named in the index body.
    positions = [
        text.index("People who use the app"),
        text.index("Group admins"),
        text.index("Frontend developers"),
        text.index("Backend developers"),
    ]
    assert positions == sorted(positions)
    # Every Phase 18 chapter slice is reachable from the index.
    for slice_id in ("B-182", "B-188", "B-189", "B-196", "B-197", "B-199"):
        assert slice_id in text


def test_shipped_diagrams_all_parse():
    """Every mermaid block in docs/, submission/ and root .md is sound."""
    failures: list[str] = []
    for target in [ROOT / "docs", ROOT / "submission", *sorted(ROOT.glob("*.md"))]:
        for md in checker.iter_markdown([target]):
            failures.extend(str(f) for f in checker.check_file(md))
    assert failures == [], "\n".join(failures)


def test_broken_diagram_fails_by_file(tmp_path):
    """Acceptance: an unclosed bracket fails, naming its file."""
    bad = tmp_path / "broken.md"
    bad.write_text(
        "# Fixture\n\n```mermaid\ngraph TD\n  A[Start --> B\n```\n",
        encoding="utf-8",
    )
    failures = checker.check_file(bad)
    assert failures, "the broken fixture must fail the gate"
    assert str(bad) in failures[0]


def test_unknown_diagram_type_fails_by_file(tmp_path):
    """A first line Mermaid cannot render is a failure, by file."""
    bad = tmp_path / "not_a_diagram.md"
    bad.write_text(
        "```mermaid\nbananaDiagram\n  A --> B\n```\n", encoding="utf-8"
    )
    failures = checker.check_file(bad)
    assert failures and str(bad) in failures[0]


def test_unterminated_fence_fails_by_file(tmp_path):
    """A fence that never closes is a failure, by file."""
    bad = tmp_path / "open_fence.md"
    bad.write_text("```mermaid\ngraph TD\n  A --> B\n", encoding="utf-8")
    failures = checker.check_file(bad)
    assert failures and str(bad) in failures[0]


def test_user_guide_1_covers_its_roadmap_topics():
    """B-182: the start + groups chapter exists and covers every
    topic its roadmap line names — account, sign-in incl. MFA,
    creating a group, inviting, roles, group settings,
    notification preferences, quiet hours — as tasks."""
    chapter = ROOT / "docs" / "01-user-guide-start-and-groups.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "register", "magic link", "two-factor", "create a group",
        "invite", "roles", "group settings", "notification preferences",
        "quiet hours", "last-owner",
    ):
        assert topic in text, f"B-182 chapter is missing its topic: {topic}"
    # Task-shaped, per the B-181 rules: a completable checklist.
    assert "first success" in text and "- [ ]" in text
    # Honesty markers the code demands: no MFA recovery codes
    # exist in this build, and the Messenger driver is unavailable.
    assert "no mfa recovery codes" in text
    assert "driver_unavailable" in text
    # The index links the built chapter.
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "01-user-guide-start-and-groups.md" in index


def test_user_guide_2_covers_every_way_in():
    """B-183: the sources chapter covers every way in its
    roadmap line names, the permission record in plain words,
    and what revoking a source does to its data."""
    chapter = ROOT / "docs" / "02-user-guide-sources.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "paste a chat", "upload a file", "newsletter", "flyer",
        "noticeboard", "paste a link", "forward an email",
        "voice note", "live chat", "granted_by", "granted_scope",
        "source_deleted_at", "30 days",
    ):
        assert topic in text, f"B-183 chapter is missing its topic: {topic}"
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "02-user-guide-sources.md" in index


def test_user_guide_3_covers_the_trust_workflow():
    """B-184: the review-queue chapter covers reading a
    candidate, confidence and the flag vocabulary, provenance
    quotes and flyer regions, editing, approve / reject /
    merge, change candidates, and contradiction resolution."""
    chapter = ROOT / "docs" / "03-user-guide-review-queue.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "candidate", "confidence", "provenance", "supported: false",
        "region", "low_confidence", "ambiguous_date", "unresolved_date",
        "conflicting", "possible_duplicate", "edited", "approve",
        "reject", "merge", "event_change", "change_target_unknown",
        "contradiction", "seat_cannot_approve", "review_min_role",
        "approvals_required", "source_deleted_at",
    ):
        assert topic in text, f"B-184 chapter is missing its topic: {topic}"
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "03-user-guide-review-queue.md" in index


def test_user_guide_4_covers_calendar_and_events():
    """B-185: the calendar chapter covers the views, agenda,
    the tonight view, event pages, discussion, RSVP and the
    waitlist, .ics, Google add, the calendar feed, print."""
    chapter = ROOT / "docs" / "04-user-guide-calendar-and-events.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "agenda", "month", "tonight", "15:00", "discussion",
        "rsvp", "waitlist", "next-in-line", ".ics",
        "google", "calendar feed", "print", "conflicts",
        "if-match", "cancel", "clone", "recurrence",
    ):
        assert topic in text, f"B-185 chapter is missing its topic: {topic}"
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "04-user-guide-calendar-and-events.md" in index


def test_user_guide_5_covers_planning():
    """B-186: the planning chapter covers tasks and the owner
    law, the decisions log, open questions and gaps, polls,
    checklists and roles, supplies, budget-lite, the
    availability finder, and templates."""
    chapter = ROOT / "docs" / "05-user-guide-planning.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "tasks", "suggested owner", "never assigns a silent victim",
        "decisions", "supersede", "open question", "gaps",
        "polls", "apply the winner", "checklists", "role slots",
        "supplies", "integer cents", "availability",
        "templates", "club night",
    ):
        assert topic in text, f"B-186 chapter is missing its topic: {topic}"
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "05-user-guide-planning.md" in index


def test_user_guide_6_covers_reminders_digests_memory():
    """B-187: the reminders/digests/memory chapter covers the
    reminder rules and their defaults, change alerts, the
    weekly digest, asking the group memory with verified
    citations and its honest refusal, briefings and recaps,
    and what the AI may and may not do."""
    chapter = ROOT / "docs" / "06-user-guide-reminders-digests-memory.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "reminder rules", "7 days", "morning of", "quiet hours hold",
        "urgent", "verbatim", "wording_source", "change alerts",
        "reannounce-drafts", "weekly digest", "digest_weekday",
        "digest/run", "approved history only", "not embedding rag",
        "budget_stopped", "i couldn't verify this", "briefing",
        "recap", "memory/runs", "may not",
    ):
        assert topic in text, f"B-187 chapter is missing its topic: {topic}"
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "06-user-guide-reminders-digests-memory.md" in index


def test_admin_guide_8_covers_dangerous_buttons_consequence_first():
    """B-188: the admin + operator guide covers group
    administration, agent seats, integrations (Facebook,
    Google, Samtal, webhooks), the AI budget, audit reading,
    data export, group erasure, and member data requests —
    dangerous buttons with consequences before instructions."""
    chapter = ROOT / "docs" / "07-admin-and-operator-guide.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "settings pack", "agent seats", "shown once",
        "seat_cannot_approve", "integrations", "facebook",
        "google", "samtal", "webhooks", "health-board",
        "reconcile", "ai_daily_budget_micros", "audit/verify",
        "users/me/data", "export", "erase", "exact name",
        "irreversible", "consequence first",
    ):
        assert topic in text, f"B-188 chapter is missing its topic: {topic}"
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "07-admin-and-operator-guide.md" in index


def test_architecture_pack_covers_its_six_diagrams():
    """B-189: the architecture pack carries the six diagrams
    its roadmap line names — system context, process view,
    module map, request lifecycle, job lifecycle, deployment
    topology — each with a prose walking tour, verified
    against the module map's own names and the job chassis'
    real states."""
    chapter = ROOT / "docs" / "08-architecture-diagram-pack.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "system context", "process view", "module map",
        "request lifecycle", "job lifecycle",
        "deployment topology", "walking tour",
        "gpa-worker", "gpa-arq-worker", "claim",
        "backoff", "dead", "commit-before-answer",
        "deps.py", "sqlite", "postgresql",
        "no router imports a model", "project_memory_map",
    ):
        assert topic in text, f"B-189 chapter is missing its topic: {topic}"
    # Six diagrams, no fewer: the roadmap line names six.
    assert text.count("```mermaid") >= 6
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "08-architecture-diagram-pack.md" in index


def test_module_atlas_covers_every_module():
    """B-190: the module atlas carries one chapter per module
    in the B-161 map — each with its job, public surface,
    tables owned, internal operations offered and consumed,
    invariants, failure modes, and its diagram — verified
    against the registry's own operation names and the
    models' own table names."""
    chapter = ROOT / "docs" / "09-module-atlas.md"
    assert chapter.exists()
    text = chapter.read_text(encoding="utf-8").lower()
    for topic in (
        "identity", "groups", "sources", "extraction",
        "events", "calendar", "planning", "nonprofit",
        "notifications", "integrations", "memory", "truth",
        "jobs", "audit", "crypto", "internal", "storage",
        "platform", "privacy", "demo", "composition",
        "tables owned", "internal operations",
        "offered", "consumed", "invariants",
        "failure modes", "public surface",
        "candidates.create", "events.publish",
        "notify.request", "notify.rsvp_promotion",
        "jobs.enqueue", "ai.submit_job", "integrations.emit",
        "no single `api.py`", "seat_cannot_approve",
        "commit-before-answer",
    ):
        assert topic in text, f"B-190 chapter is missing its topic: {topic}"
    # One diagram per module chapter: 22 chapters.
    assert text.count("```mermaid") >= 22
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "09-module-atlas.md" in index


def test_sound_diagram_passes(tmp_path):
    """The gate is not a blanket refusal: a sound diagram passes."""
    good = tmp_path / "sound.md"
    good.write_text(
        "```mermaid\ngraph TD\n  A[Start] --> B{Decide}\n```\n",
        encoding="utf-8",
    )
    assert checker.check_file(good) == []
