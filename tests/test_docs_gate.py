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


def test_sound_diagram_passes(tmp_path):
    """The gate is not a blanket refusal: a sound diagram passes."""
    good = tmp_path / "sound.md"
    good.write_text(
        "```mermaid\ngraph TD\n  A[Start] --> B{Decide}\n```\n",
        encoding="utf-8",
    )
    assert checker.check_file(good) == []
