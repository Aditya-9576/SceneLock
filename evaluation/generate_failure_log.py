"""Extract real keyword-baseline mistakes without inventing Gemini mistakes."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evaluation" / "phase9_failure_log.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    samples = {row["test_id"]: row for row in read_json(ROOT / "sample_inputs" / "test_cases.json")["cases"]}
    expected = {row["test_id"]: row for row in read_json(ROOT / "evaluation" / "expected_labels.json")["labels"]}
    predictions = {row["test_id"]: row for row in read_json(ROOT / "evaluation" / "baseline_predictions.json")["predictions"]}
    baseline_summary = read_json(ROOT / "evaluation" / "baseline_summary.json")
    observed_errors = {(row["test_id"], row["error"]) for row in baseline_summary["errors"]}
    selected = (("T06", "false_positive"), ("T14", "false_negative"))
    for pair in selected:
        if pair not in observed_errors:
            raise ValueError("Baseline results changed: expected actual error was not observed.")

    explanation = {
        "T06": {
            "root_cause": "The frozen keyword baseline reads screenplay/prompt tokens but ignores shot_type and shot_intent, demanding an earlier off-frame key-hiding action during a reaction close-up.",
            "correction": "Added explicit before/after shot-scope counterchecks to Gemini instructions v3; baseline v1 is intentionally unchanged as a reproducible yardstick.",
        },
        "T14": {
            "root_cause": "Enough keywords overlap although the giver and recipient of the antidote are reversed; lexical recall cannot represent role assignments.",
            "correction": "Added explicit actor/receiver direction countercheck to Gemini instructions v3; baseline v1 remains frozen.",
        },
    }
    mistakes = []
    for cid, error_type in selected:
        sample, label, prediction = samples[cid], expected[cid], predictions[cid]
        mistakes.append({
            "case_id": cid,
            "actual_predictor": "keyword_overlap_v1_not_an_LLM",
            "observed_error": error_type,
            "screenplay_text": sample["screenplay_text"],
            "video_prompt": sample["video_prompt"],
            "shot_type": sample["shot_type"],
            "shot_intent": sample["shot_intent"],
            "observed_prediction": {
                "has_confirmed_issue": prediction["predicted_has_confirmed_issue"],
                "lexical_recall": prediction["lexical_recall"],
            },
            "expected_overall_status": label["expected_overall_status"],
            "expected_fact_statuses": [f["expected_status"] for f in label["expected_facts"]],
            **explanation[cid],
            "retest": {
                "baseline": "Same mistake reproducibly persists (frozen baseline).",
                "new_Gemini_instructions": "Static instruction tests passed; real model retest blocked by missing key.",
            },
        })

    log = {
        "important": "These are actual keyword-BASELINE mistakes, not Gemini mistakes. No Gemini API key was available.",
        "observed_baseline_errors": mistakes,
        "actual_implementation_regressions_fixed": [
            {
                "id": "CODE-01",
                "original_failure": "Zero-width Unicode-only input and evidence were accepted as visible text.",
                "root_cause": "str.strip() does not remove U+200B/U+200C/U+200D.",
                "correction": "Schema and quote validator now require visible Unicode characters.",
                "retest": "test_phase9_adversarial.py: invisible input, custom intent and evidence checks pass.",
            },
            {
                "id": "CODE-02",
                "original_failure": "Raw responses from rejected or incomplete provider output were unavailable to the evaluator.",
                "root_cause": "Adapter previously validated/rejected before a raw-response observer could receive the unmodified text.",
                "correction": "Optional evaluation observer captures provider text before status and evidence checks; exclusive raw archive uses exact T01_response.json names.",
                "retest": "test_gemini_integration.py: both malformed/evidence-invalid and incomplete responses were captured and the reports rejected.",
            },
        ],
        "model_mistake_observed": False,
        "model_fix_retest_completed": False,
        "live_model_blocker": "No configured Gemini API key; cannot honestly identify or retest an actual Gemini mistake.",
    }
    OUTPUT.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE: {OUTPUT} | verified baseline mistakes: {len(mistakes)}")


if __name__ == "__main__":
    main()
