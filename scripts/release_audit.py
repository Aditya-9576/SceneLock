"""Pre-publish check for accidentally tracked secrets or private raw outputs.

Uses git's staged/tracked file list when available. Otherwise scans the
release-shaped project tree excluding local caches and virtual environments.
This heuristic cannot prove every screenplay is public; humans must review
the content before sharing a repository.

Run: python scripts/release_audit.py
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SOURCE_EXTENSIONS = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt", ".csv"}
SECRET_MARKERS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"ghp_[0-9A-Za-z]{35,}"),
    re.compile(r"github_pat_[0-9A-Za-z_]{40,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
BLOCKED_SUFFIXES = {".key", ".pem", ".p8", ".p12"}
SKIP_DIRECTORIES = {".git", ".venv", "venv", ".pytest_cache", "__pycache__", ".mypy_cache"}


def candidate_paths(project: Path) -> list[Path]:
    if (project / ".git").exists():
        tracked = subprocess.run(
            ["git", "ls-files", "--cached", "-z"], cwd=project,
            capture_output=True, check=True,
        )
        if tracked.stdout:
            return [project / item.decode("utf-8") for item in tracked.stdout.split(b"\0") if item]

    found: list[Path] = []
    for directory, folders, names in os.walk(project):
        folders[:] = [name for name in folders if name not in SKIP_DIRECTORIES]
        found.extend(Path(directory) / name for name in names)
    return found


def audit(project: Path = PROJECT) -> tuple[int, list[str]]:
    messages: list[str] = []
    paths = candidate_paths(project)
    for path in paths:
        relative = path.relative_to(project).as_posix()
        parts = Path(relative).parts
        basename = path.name.lower()
        if (
            basename == ".env"
            or (basename.startswith(".env.") and basename != ".env.example")
            or relative == ".streamlit/secrets.toml"
            or (parts and parts[0] == "raw_outputs" and relative != "raw_outputs/README.md")
            or path.suffix.lower() in BLOCKED_SUFFIXES
            or basename == "credentials.json"
            or basename.startswith("service-account") and path.suffix.lower() == ".json"
        ):
            messages.append(f"Forbidden public file: {relative}")
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        if any(marker.search(content) for marker in SECRET_MARKERS):
            messages.append(f"Potential credential detected in: {relative} (value not displayed)")

    return len(paths), messages


def main() -> int:
    count, errors = audit()
    if errors:
        print("RELEASE AUDIT FAILED — do not publish these files:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"RELEASE AUDIT PASSED: {count} publishable files checked; no detected secrets or raw outputs.")
    print("Manual content review is still required before public publication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
