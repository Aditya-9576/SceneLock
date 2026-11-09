"""Tests for the frozen Phase 1 five-group input contract."""

import pytest

from schemas import AnalysisInput, ShotType
from validators import InputValidationError, evidence_is_exact_substring, validate_input_payload


def valid_payload() -> dict:
    return {
        "screenplay_text": "Mina opens the wooden door and looks down the corridor.",
        "video_prompt": "Mina pushes open a wooden door and looks into a corridor.",
        "shot_type": ShotType.ACTION_SHOT.value,
        "shot_intent": "Show the door opening.",
        "episode_id": "EP01",
        "scene_id": "SC02",
        "shot_id": "SH03",
    }


def test_valid_input_parses_and_trims() -> None:
    data = valid_payload()
    data["screenplay_text"] = "  " + data["screenplay_text"] + "  "
    model = validate_input_payload(data)
    assert model.screenplay_text == data["screenplay_text"].strip()
    assert model.shot_type == ShotType.ACTION_SHOT


@pytest.mark.parametrize("field", ["screenplay_text", "video_prompt"])
def test_required_text_cannot_be_blank(field: str) -> None:
    data = valid_payload()
    data[field] = "   "
    with pytest.raises(InputValidationError) as exc_info:
        validate_input_payload(data)
    assert field.replace("_", " ") in str(exc_info.value).lower()


def test_shot_type_is_required() -> None:
    data = valid_payload()
    data["shot_type"] = None
    with pytest.raises(InputValidationError, match="Shot type"):
        validate_input_payload(data)


def test_custom_shot_requires_intent() -> None:
    data = valid_payload()
    data["shot_type"] = ShotType.CUSTOM_OTHER.value
    data["shot_intent"] = ""
    with pytest.raises(InputValidationError, match="requires a short shot-intent"):
        validate_input_payload(data)


def test_custom_shot_with_intent_is_valid() -> None:
    data = valid_payload()
    data["shot_type"] = ShotType.CUSTOM_OTHER.value
    assert validate_input_payload(data).shot_type == ShotType.CUSTOM_OTHER


def test_optional_identifiers_can_be_empty() -> None:
    data = valid_payload()
    data.update({"episode_id": " ", "scene_id": "", "shot_id": " ", "shot_intent": " "})
    model = validate_input_payload(data)
    assert model.episode_id is None
    assert model.scene_id is None
    assert model.shot_id is None
    assert model.shot_intent is None


def test_length_caps_are_enforced() -> None:
    data = valid_payload()
    data["screenplay_text"] = "x" * 8001
    with pytest.raises(InputValidationError):
        validate_input_payload(data)


def test_hindi_and_english_unicode_are_preserved() -> None:
    data = valid_payload()
    data["screenplay_text"] = "रीमा लाल dupatta पहनकर दरवाज़ा खोलती है।"
    model = validate_input_payload(data)
    assert model.screenplay_text == data["screenplay_text"]


def test_extra_fields_are_rejected() -> None:
    data = valid_payload()
    data["hidden_accuracy_score"] = 99
    with pytest.raises(InputValidationError):
        validate_input_payload(data)


def test_evidence_uses_exact_source_substrings() -> None:
    assert evidence_is_exact_substring("red dress", "She wears a red dress.")
    assert not evidence_is_exact_substring("blue dress", "She wears a red dress.")
    assert not evidence_is_exact_substring("", "Any text")


def test_all_seven_shot_types_validate() -> None:
    for option in ShotType:
        data = valid_payload()
        data["shot_type"] = option.value
        data["shot_intent"] = "A specific shot." if option == ShotType.CUSTOM_OTHER else ""
        assert isinstance(AnalysisInput.model_validate(data), AnalysisInput)
