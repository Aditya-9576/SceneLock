"""One-time, private local API key setup for non-coders on macOS.

Prompts in the local Terminal without echoing the key. Saves it only to the
git-ignored .streamlit/secrets.toml with owner-only permissions.
No network request is made and no credential is printed.
"""

from __future__ import annotations

import json
import os
import tempfile
from getpass import getpass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"


def save_key_securely(key: str, target: Path = SECRETS_PATH) -> None:
    value = key.strip()
    if not value or value.upper() in {"YOUR_API_KEY_HERE", "YOUR_KEY_HERE"}:
        raise ValueError("An actual Gemini API key is required.")
    if target.exists():
        raise FileExistsError("A secrets file already exists. It was not overwritten.")

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".secrets-", suffix=".tmp", dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("GEMINI_API_KEY = " + json.dumps(value) + "\n")
            handle.write('GEMINI_MODEL = "gemini-3.6-flash"\n')
        # Exclusive creation avoids overwriting a concurrent or existing file.
        os.link(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    if SECRETS_PATH.exists():
        print("A local Gemini secrets file already exists. No changes were made.")
        return 0
    print("SceneLock private Gemini key setup. The key will not be displayed.")
    key = getpass("Paste your Gemini API key here (typing will be hidden): ")
    try:
        save_key_securely(key)
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"Setup could not finish: {type(exc).__name__}. No existing key was changed.")
        return 1
    print("Key saved privately on this computer. It is ignored by Git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
