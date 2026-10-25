"""Phase 17 migration tests (roadmap B-003 discipline).

Revision 0017 adds one table — ``group_keys``, the per-group
wrapped data keys of the field-encryption service (B-167).
It must take a Phase 13-era database UP and back DOWN
cleanly, and sit happily on top of the guarded 0001 that
builds from live metadata (where the table already exists
and 0017 is a no-op).
"""

import os
import sqlite3
import subprocess
import sys


def _alembic(tmp_path, *args):
    url = "sqlite:///" + str(tmp_path / "mig.db")
    env = {**os.environ, "GPA_DATABASE_URL": url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(_repo_root()), env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result


def _repo_root():
    from pathlib import Path

    return Path(__file__).resolve().parent.parent


def _tables(tmp_path) -> set[str]:
    conn = sqlite3.connect(tmp_path / "mig.db")
    try:
        return {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()


def test_phase17_migration_up_down_up(tmp_path):
    # The chain's shape (the phase-13 note): 0001 builds from
    # LIVE metadata, so a fresh database carries group_keys
    # from the start and 0017's guarded create is a no-op
    # there. What 0017 must prove is its own guarded down/up
    # on a database at head.
    _alembic(tmp_path, "upgrade", "head")
    assert "group_keys" in _tables(tmp_path)

    _alembic(tmp_path, "downgrade", "0016_phase13_privacy")
    assert "group_keys" not in _tables(tmp_path)

    _alembic(tmp_path, "upgrade", "0017_phase17_crypto")
    assert "group_keys" in _tables(tmp_path)


def test_phase17_migration_from_scratch_is_a_noop(tmp_path):
    # The fresh-database road: upgrade straight to head; the
    # guarded create must not collide with 0001's metadata
    # build, and the chain must end at 0017.
    result = _alembic(tmp_path, "upgrade", "head")
    assert "group_keys" in _tables(tmp_path)
    heads = _alembic(tmp_path, "current")
    assert "0017_phase17_crypto" in heads.stdout
