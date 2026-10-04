#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "scripts" / "release-files.json"
EXCLUDED_NAMES = {".DS_Store", "AGENTS.md", "AGENTS.override.md", "AGENTS.local.md"}
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "data", "dist", "output", "reports", "tmp"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config() -> dict[str, object]:
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("unsupported release-files.json schema")
    return value


def version() -> str:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(metadata["project"]["version"])


def allowed_files(config: dict[str, object]) -> list[Path]:
    if config.get("trees"):
        raise ValueError("Release trees are not supported; enumerate reviewed files explicitly")
    selected: set[Path] = set()
    for relative in config.get("files", []):
        relative = Path(str(relative))
        if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative):
            raise ValueError("Release path must stay inside the source root")
        path = ROOT / relative
        if (EXCLUDED_PARTS.intersection(relative.parts) or path.name in EXCLUDED_NAMES
                or any(part in str(relative).casefold() for part in (".local.", ".private."))
                or any(p in {"private", "profiles", "credentials", "sessions"} for p in relative.parts)
                or path.name.startswith(".env")):
            raise ValueError("Private artifacts must not be explicitly packaged")
        if any((ROOT / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError("Release paths must not traverse symlinks")
        if not path.is_file():
            raise FileNotFoundError(f"release file is missing: {relative}")
        selected.add(path)
    return sorted(selected, key=lambda path: path.relative_to(ROOT).as_posix())


def copy_release(files: list[Path], destination: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for source in files:
        relative = source.relative_to(ROOT)
        target = destination / relative
        if source.is_symlink():
            raise ValueError(f"release does not allow symlinks: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        executable = source.suffix in {".py", ".sh"} and source.parent.name == "scripts"
        target.chmod(0o755 if executable else 0o644)
        entries.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256(target),
                "size": target.stat().st_size,
            }
        )
    return entries


def write_manifest(destination: Path, package_name: str, package_version: str, entries: list[dict[str, object]]) -> Path:
    manifest = destination / "RELEASE-MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": package_name,
                "version": package_version,
                "contains_git_history": False,
                "contains_user_state": False,
                "files": entries,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest.chmod(0o644)
    return manifest


def privacy_check(destination: Path) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "privacy_check.py"), "--root", str(destination), "--all-files"],
        cwd=ROOT,
        check=True,
    )


def write_zip(source: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source.parent).as_posix()):
            if not path.is_file():
                continue
            archive_name = path.relative_to(source.parent).as_posix()
            info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (path.stat().st_mode & 0o777) << 16
            info.create_system = 3
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output_root: Path) -> dict[str, object]:
    config = load_config()
    package_name = str(config["package_name"])
    package_version = version()
    release_name = f"{package_name}-{package_version}"
    output_root.mkdir(parents=True, exist_ok=True)
    final_dir = output_root / release_name
    final_zip = output_root / f"{release_name}.zip"
    with tempfile.TemporaryDirectory(prefix="job-research-release-", dir=output_root) as temporary:
        staging = Path(temporary) / release_name
        staging.mkdir()
        entries = copy_release(allowed_files(config), staging)
        manifest = write_manifest(staging, package_name, package_version, entries)
        privacy_check(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.copytree(staging, final_dir)
        write_zip(staging, final_zip)
    return {
        "status": "built",
        "release_directory": str(final_dir),
        "archive": str(final_zip),
        "archive_sha256": sha256(final_zip),
        "manifest_sha256": sha256(final_dir / manifest.name),
        "file_count": len(entries) + 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a privacy-checked source bundle without Git history.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    result = build(args.output.expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
