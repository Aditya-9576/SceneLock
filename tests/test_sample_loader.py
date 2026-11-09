"""Demo loads contain only real user inputs, never expected model answers."""

from sample_loader import DEMO_LABELS, INPUT_FIELDS, demo_samples
from schemas import AnalysisInput


def test_demo_catalog_is_complete_and_contains_only_form_inputs():
    choices = demo_samples()
    assert len(choices) == len(DEMO_LABELS) == 6
    assert list(choices)[0].startswith("T01")
    for values in choices.values():
        assert set(values) == set(INPUT_FIELDS)
        assert "expected_labels" not in values
        assert "scenario" not in values
        assert "tags" not in values
        assert "test_id" not in values
        assert AnalysisInput.model_validate(values)


def test_important_live_demo_examples_are_available():
    labels = list(demo_samples())
    for case_id in ("T01", "T03", "T05", "T06", "T09", "T15"):
        assert any(label.startswith(case_id) for label in labels)
