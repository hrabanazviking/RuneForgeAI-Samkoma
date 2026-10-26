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


def test_sound_diagram_passes(tmp_path):
    """The gate is not a blanket refusal: a sound diagram passes."""
    good = tmp_path / "sound.md"
    good.write_text(
        "```mermaid\ngraph TD\n  A[Start] --> B{Decide}\n```\n",
        encoding="utf-8",
    )
    assert checker.check_file(good) == []
