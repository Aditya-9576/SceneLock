"""Raw-response preservation is optional, exact and resistant to overwrite."""

from __future__ import annotations

import os

import pytest

from raw_archive import save_raw_case_response, save_raw_evaluation_response


def test_raw_archive_preserves_exact_unicode_json_and_line_endings(tmp_path) -> None:
    original = '{\r\n  "prompt": "रीमा, \"रुको\"",\r\n  "note": "line\\nnext"\r\n}\r\n'
    target = save_raw_evaluation_response(
        original, case_id="P8-UNICODE", analysis_id="run_123", output_dir=tmp_path
    )
    assert target.read_bytes() == original.encode("utf-8")
    assert target.name == "P8-UNICODE_run_123.json"
    if os.name == "posix":
        assert target.stat().st_mode & 0o777 == 0o600


def test_raw_archive_never_overwrites_a_previous_result(tmp_path) -> None:
    previous = save_raw_evaluation_response(
        '{"a": 1}', case_id="T01", analysis_id="123", output_dir=tmp_path
    )
    with pytest.raises(FileExistsError):
        save_raw_evaluation_response('{"a": 2}', case_id="T01", analysis_id="123", output_dir=tmp_path)
    assert previous.read_text(encoding="utf-8") == '{"a": 1}'


@pytest.mark.parametrize("bad_case", ["../outside", "T 01", "T01/sub", ".hidden", "", "😄"])
def test_raw_archive_rejects_unsafe_case_ids(tmp_path, bad_case: str) -> None:
    with pytest.raises(ValueError, match="Invalid case_id"):
        save_raw_evaluation_response('{"ok": true}', case_id=bad_case, analysis_id="123", output_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_raw_archive_rejects_blank_or_unsafe_analysis_id(tmp_path) -> None:
    with pytest.raises(ValueError):
        save_raw_evaluation_response('{"ok": true}', case_id="T01", analysis_id="..", output_dir=tmp_path)
    with pytest.raises(ValueError):
        save_raw_evaluation_response(" \n ", case_id="T01", analysis_id="ok", output_dir=tmp_path)


def test_phase9_raw_filename_contract_and_exact_bytes(tmp_path) -> None:
    raw = '{"unmodified": "रीमा, opened"}\r\n'
    path = save_raw_case_response(raw, case_id="T15", output_dir=tmp_path)
    assert path.name == "T15_response.json"
    assert path.read_bytes() == raw.encode("utf-8")
    with pytest.raises(FileExistsError):
        save_raw_case_response("different", case_id="T15", output_dir=tmp_path)
    assert path.read_bytes() == raw.encode("utf-8")


@pytest.mark.parametrize("bad_case_id", ["T00", "T16", "T01/../../x", "U04", "T1", "T01_response"])
def test_phase9_raw_filename_rejects_non_eval_identifiers(tmp_path, bad_case_id) -> None:
    with pytest.raises(ValueError, match="Expected an evaluation ID"):
        save_raw_case_response('{"ok": true}', case_id=bad_case_id, output_dir=tmp_path)

