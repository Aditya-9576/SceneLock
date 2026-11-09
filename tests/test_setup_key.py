"""Test secure local key storage with fake values only."""

import os

import pytest

from scripts.setup_gemini_key import save_key_securely


def test_saves_fake_key_in_owner_only_file(tmp_path):
    target = tmp_path / "private" / "secrets.toml"
    save_key_securely("fake-unit-test-key", target)
    content = target.read_text(encoding="utf-8")
    assert 'GEMINI_API_KEY = "fake-unit-test-key"' in content
    assert 'GEMINI_MODEL = "gemini-3.6-flash"' in content
    assert os.stat(target).st_mode & 0o777 == 0o600


def test_does_not_overwrite_existing_secret(tmp_path):
    target = tmp_path / "secrets.toml"
    target.write_text("original-secret", encoding="utf-8")
    with pytest.raises(FileExistsError):
        save_key_securely("new-fake-secret", target)
    assert target.read_text(encoding="utf-8") == "original-secret"


def test_rejects_placeholder(tmp_path):
    target = tmp_path / "secrets.toml"
    with pytest.raises(ValueError):
        save_key_securely("YOUR_API_KEY_HERE", target)
    assert not target.exists()
