#!/usr/bin/env python3
"""Build a release ZIP (roadmap B-010; anatomy in roadmap §8).

    uv run python scripts/make_release_zip.py ZIP-0

The ZIP carries the source, the frozen OPENAPI.json, the generated
TypeScript types, the Bruno collection, run/test scripts, and a
manifest.json naming every file with its SHA-256 — plus a sidecar
``<name>.zip.sha256`` so a receiver can verify the whole archive.
Excluded, always: .git, virtualenvs, caches, databases, runtime
data, and ANY .env file — a ZIP must never carry a secret (D-25).
"""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "data", "releases", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".db", ".db-wal", ".db-shm", ".sqlite", ".sqlite3", ".log", ".zip"}


def _included(path: Path) -> bool:
    """Is this file allowed into a release ZIP?"""
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False  # Real env files are secrets; only the example ships.
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "ZIP-0"
    out_dir = ROOT / "releases"
    out_dir.mkdir(exist_ok=True)
    zip_path = out_dir / f"group-planning-assistant-backend-{name}.zip"

    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and _included(p))
    manifest = {"release": name, "files": {}}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = str(path.relative_to(ROOT))
            data = path.read_bytes()
            manifest["files"][rel] = hashlib.sha256(data).hexdigest()
            zf.writestr(rel, data)
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (out_dir / f"{zip_path.name}.sha256").write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    print(f"Built {zip_path} ({zip_path.stat().st_size:,} bytes, {len(files)} files)")
    print(f"sha256: {digest}")


if __name__ == "__main__":
    main()
