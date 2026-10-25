"""In-place upgrade (roadmap B-156).

    uv run python scripts/upgrade.py --zip releases/gpa-backend-vX.Y-DATE.zip \
        [--root /opt/gpa] [--env-file /etc/gpa/gpa.env]

The order is the roadmap's, and it is not negotiable:

1. **Backup.** The CURRENT tree's own backup script takes a
   bundle of the live deployment (database + storage +
   manifest). The bundle's hashes are re-verified here
   before anything else happens — an upgrade that cannot
   prove its way back does not start.
2. **Stage + build.** The new ZIP is unpacked beside the
   installation and given a FRESH virtualenv from its own
   lockfile (a copied venv is a broken venv — B-146).
3. **Migrate.** The staged tree's Alembic migrations run
   against the LIVE database. If this fails, nothing has
   been swapped; the way back is step 1's bundle.
4. **Smoke.** The staged server boots against the real
   (now migrated) deployment data on a scratch port and
   must answer /health with status ok before it may serve.
5. **Serve (the swap).** The old tree moves aside to
   ``<root>.previous-<stamp>``; the staged tree takes the
   root's path, carrying the deployment's data/, backups/
   and .env with it. The script then prints the restart
   commands — restarting the service is the operator's
   deliberate act, not a script's side effect.

**Rollback is "restore the backup," stated plainly:** swap
the two directories back and place the bundle with
scripts/restore.py (the exact commands are printed at the
end of every run and live in DEPLOYMENT.md).

The tool ships with the backend from B-156 on. Upgrading
an installation older than that (the drill: v0.4 → v0.5)
runs this script from a checkout of the new code — the
--root flag exists for exactly that.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class UpgradeError(Exception):
    """A plain-words stop: the upgrade does not proceed."""


def _run(command: list[str], *, cwd: Path, env: dict | None = None) -> None:
    """Run one step, loudly. Any failure stops the upgrade."""
    print(f"  $ {' '.join(command)}  (in {cwd})")
    result = subprocess.run(command, cwd=cwd, env=env)
    if result.returncode != 0:
        raise UpgradeError(
            f"step failed with exit {result.returncode}: {command[0]} "
            "— the installation has NOT been swapped; see the "
            "rollback note if migrations already ran."
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_bundle(bundle: Path) -> None:
    """Re-check every hash in a backup bundle's manifest.

    The upgrade's rollback is only real if the bundle is —
    so the bundle proves itself here, the same check
    scripts/restore.py runs before placing anything.
    """
    manifest_path = bundle / "manifest.json"
    if not manifest_path.is_file():
        raise UpgradeError(f"backup bundle has no manifest: {bundle}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files", []):
        path = bundle / entry["path"]
        if not path.is_file():
            raise UpgradeError(f"backup bundle is missing {entry['path']}")
        if _sha256(path) != entry["sha256"]:
            raise UpgradeError(
                f"backup bundle file {entry['path']} fails its hash — "
                "the way back is not proven; refusing to upgrade."
            )


def read_env_file(path: Path | None) -> dict[str, str]:
    """Parse a GPA env file (KEY=VALUE lines) for subprocesses.

    Deliberately a parser, never a shell source: values are
    data, not code. Only GPA_* keys are carried over.
    """
    values: dict[str, str] = {}
    if path is None:
        return values
    if not path.is_file():
        raise UpgradeError(f"env file not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip().startswith("GPA_"):
            values[key.strip()] = value.strip()
    return values


def stage_zip(zip_path: Path, stage_dir: Path) -> Path:
    """Unpack a release ZIP; return the staged tree's root.

    The §8 anatomy puts the runnable tree under gpa-backend/
    inside the ZIP; the manifest must agree, or this is not
    a GPA release and the upgrade refuses it.
    """
    if not zip_path.is_file():
        raise UpgradeError(f"release ZIP not found: {zip_path}")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if "release-manifest.json" not in names:
            raise UpgradeError(
                f"{zip_path.name} has no release-manifest.json — "
                "not a GPA release ZIP (see the roadmap, §8)."
            )
        manifest = json.loads(archive.read("release-manifest.json"))
        archive.extractall(stage_dir)
    staged = stage_dir / "gpa-backend"
    if not (staged / "pyproject.toml").is_file():
        raise UpgradeError("the ZIP's gpa-backend/ tree is missing pyproject.toml")
    print(f"  staged {manifest.get('version', '?')} "
          f"(git {manifest.get('git_hash', '?')[:9]}) at {staged}")
    return staged


def smoke(staged: Path, env: dict[str, str], *, port: int) -> None:
    """Boot the staged tree against the deployment and ask it
    the one question that matters: /health, status ok."""
    process_env = dict(os.environ) | env
    process = subprocess.Popen(
        [
            str(staged / ".venv" / "bin" / "uvicorn"),
            "gpa.main:create_app", "--factory",
            "--host", "127.0.0.1", "--port", str(port),
        ],
        cwd=staged,
        env=process_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 60
        while time.time() < deadline:
            if process.poll() is not None:
                raise UpgradeError(
                    "the staged server exited during smoke — "
                    "read its log by booting it by hand."
                )
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health", timeout=3
                ) as response:
                    body = json.loads(response.read())
                if body.get("status") == "ok":
                    print(f"  smoke ok: /health on :{port} → status ok, "
                          f"database {body.get('database')}")
                    return
                raise UpgradeError(f"smoke /health answered {body!r}")
            except (OSError, ValueError):
                time.sleep(1)
        raise UpgradeError("the staged server never answered /health in 60s")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def upgrade(
    *,
    root: Path,
    zip_path: Path,
    env_file: Path | None,
    database_url: str,
    storage_dir: Path,
    smoke_port: int,
    log=print,
) -> dict:
    """Run the five steps. Returns a small report dict."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    env = read_env_file(env_file)
    env.setdefault("GPA_DATABASE_URL", database_url)
    env.setdefault("GPA_STORAGE_DIR", str(storage_dir))

    if not (root / "pyproject.toml").is_file():
        raise UpgradeError(f"{root} does not look like a GPA installation.")
    # The backup runs with the CURRENT tree's own interpreter:
    # its code must import against its own environment, not
    # against whichever Python launched this script.
    venv_python = root / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else sys.executable

    # 1 — Backup, with the CURRENT tree's own script, and proof.
    log("1/5 backup (current tree's scripts/backup.py)…")
    bundle_parent = root / "backups"
    bundle_parent.mkdir(parents=True, exist_ok=True)
    bundle = bundle_parent / f"gpa-backup-{stamp}"
    _run(
        [python, "scripts/backup.py", "--out", str(bundle)],
        cwd=root,
        env=dict(os.environ) | env,
    )
    verify_bundle(bundle)
    log(f"  bundle verified: {bundle}")

    # 2 — Stage + build the new tree beside the installation.
    log("2/5 stage + build the new tree…")
    stage_dir = root.parent / f"{root.name}.staging-{stamp}"
    staged = stage_zip(zip_path, stage_dir)
    _run(["uv", "sync", "--frozen"], cwd=staged)

    # 3 — Migrate the LIVE database with the staged tree.
    log("3/5 migrate the live database (staged tree's Alembic)…")
    _run(
        [str(staged / ".venv" / "bin" / "python"), "-m", "alembic", "upgrade", "head"],
        cwd=staged,
        env=dict(os.environ) | env,
    )

    # 4 — Smoke the staged tree against the real data.
    log("4/5 smoke (staged server, real data, scratch port)…")
    smoke(staged, env, port=smoke_port)

    # 5 — The swap: data and configuration carry over; the old
    # tree stays whole, one rename away, as .previous-<stamp>.
    log("5/5 swap…")
    for carried in ("data", "backups"):
        source = root / carried
        if source.exists():
            shutil.copytree(source, staged / carried, dirs_exist_ok=True)
    if (root / ".env").exists() and not (staged / ".env").exists():
        shutil.copy2(root / ".env", staged / ".env")
    previous = root.parent / f"{root.name}.previous-{stamp}"
    root.rename(previous)
    try:
        staged.rename(root)
    except OSError:
        previous.rename(root)  # put the live tree back, then say so
        raise UpgradeError("the swap failed midway; the old tree was put back.")
    shutil.rmtree(stage_dir, ignore_errors=True)

    log("")
    log(f"Upgraded: {root} now runs the {zip_path.name} tree.")
    log(f"The previous tree is kept whole at {previous}.")
    log("Restart to serve it:")
    log("  systemctl restart gpa gpa-worker        (systemd installs)")
    log(f"  ./run.sh                                (hand-run trees, in {root})")
    log("")
    log("ROLLBACK, plainly: restore the backup —")
    log(f"  mv {root} {root.name}.failed-{stamp} && mv {previous} {root}")
    log(f"  uv run python scripts/restore.py {bundle} <scratch dir>, then point "
        "GPA_DATABASE_URL / GPA_STORAGE_DIR at the restored files (DEPLOYMENT.md).")
    return {"bundle": str(bundle), "previous": str(previous), "root": str(root)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade a GPA installation in place (B-156)."
    )
    parser.add_argument("--zip", type=Path, required=True, help="The new release ZIP")
    parser.add_argument(
        "--root", type=Path, default=ROOT,
        help="The installation to upgrade (default: this script's own tree)",
    )
    parser.add_argument(
        "--env-file", type=Path, default=None,
        help="The deployment's GPA env file (B-153 layout: /etc/gpa/gpa.env)",
    )
    parser.add_argument(
        "--database-url", default=None,
        help="Override the database URL (default: env file, else <root>/data/gpa.db)",
    )
    parser.add_argument(
        "--smoke-port", type=int, default=18777,
        help="Scratch port for the smoke boot (default 18777)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    database_url = (
        args.database_url
        or read_env_file(args.env_file).get("GPA_DATABASE_URL")
        or f"sqlite:///{root}/data/gpa.db"
    )
    storage_dir = Path(
        read_env_file(args.env_file).get("GPA_STORAGE_DIR", root / "data" / "storage")
    )
    try:
        upgrade(
            root=root,
            zip_path=args.zip,
            env_file=args.env_file,
            database_url=database_url,
            storage_dir=storage_dir,
            smoke_port=args.smoke_port,
        )
    except UpgradeError as error:
        print(f"Upgrade stopped: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
