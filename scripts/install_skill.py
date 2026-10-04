#!/usr/bin/env python3
"""Install only reviewed manifest files, retaining previous installs as backups."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
from uuid import uuid4

import build_release


def install(agent, base, replace=False):
    prefix = Path("skills/job-research-match")
    selected = [p for p in build_release.allowed_files(build_release.load_config())
                if p.relative_to(build_release.ROOT).is_relative_to(prefix)]
    parent = base / "skills"
    destination = parent / "job-research-match"
    if destination.exists() and not replace:
        raise ValueError("destination exists; use --replace")
    if destination.is_symlink() or any(p.is_symlink() for p in (parent, base, *base.parents)):
        raise ValueError("installation paths must not traverse symlinks")
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".skill-stage-", dir=base) as temporary:
        stage = Path(temporary) / "job-research-match"
        stage.mkdir()
        for source in selected:
            target = stage / source.relative_to(build_release.ROOT / prefix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o755 if source.suffix in {".py", ".sh"} else 0o644)
        build_release.privacy_check(stage)
        # Initialization creates local state only, not an agent or connector run.
        subprocess.run([sys.executable, str(stage / "scripts/local_state.py"), "init"],
                       check=True, stdout=subprocess.DEVNULL)
        backup = None
        if destination.exists():
            backups = base / "skill-backups"
            if backups.is_symlink():
                raise ValueError("backup directory must not be symlinked")
            backups.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = backups / f"job-research-match.{stamp}.{uuid4().hex[:8]}"
            destination.rename(backup)
        try:
            stage.rename(destination)
        except Exception:
            if backup is not None and not destination.exists():
                backup.rename(destination)
            raise
    print(f"{agent}: installed {len(selected)} reviewed files; on-demand use only")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("codex", "claude", "both"), required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    for agent in (("codex", "claude") if args.target == "both" else (args.target,)):
        variable, default = ("CODEX_HOME", ".codex") if agent == "codex" else ("CLAUDE_CONFIG_DIR", ".claude")
        base = Path(os.environ.get(variable, str(Path.home() / default))).expanduser().absolute()
        install(agent, base, args.replace)


if __name__ == "__main__":
    main()
