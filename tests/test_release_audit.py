"""Release gate must find real secret files, not display secret values."""

from pathlib import Path

from scripts.release_audit import audit


def test_release_scan_rejects_raw_outputs_and_secret_files(tmp_path: Path) -> None:
    (tmp_path / "raw_outputs").mkdir()
    (tmp_path / "raw_outputs" / "README.md").write_text("No raw data.\n")
    (tmp_path / "raw_outputs" / "T01_response.json").write_text('{"private": true}')
    (tmp_path / ".streamlit").mkdir()
    (tmp_path / ".streamlit" / "secrets.toml").write_text('GEMINI_API_KEY="do_not_disclose"')
    (tmp_path / ".env.local").write_text("SECRET=bad")

    scanned, warnings = audit(tmp_path)
    assert scanned == 4
    assert any("T01_response.json" in warning for warning in warnings)
    assert any("secrets.toml" in warning for warning in warnings)
    assert any(".env.local" in warning for warning in warnings)
    assert all("do_not_disclose" not in warning for warning in warnings)


def test_release_scan_rejects_obvious_credential_tokens_without_printing_them(tmp_path: Path) -> None:
    key = "AIza" + "1" * 36
    (tmp_path / "note.md").write_text(f"A bad example with credential {key}", encoding="utf-8")
    _, warnings = audit(tmp_path)
    assert len(warnings) == 1
    assert "note.md" in warnings[0]
    assert key not in warnings[0]


def test_release_scan_accepts_synthetic_examples(tmp_path: Path) -> None:
    (tmp_path / "raw_outputs").mkdir()
    (tmp_path / "raw_outputs" / "README.md").write_text("No provider files.\n")
    (tmp_path / "app.py").write_text("print('synthetic example')\n")
    _, warnings = audit(tmp_path)
    assert warnings == []
