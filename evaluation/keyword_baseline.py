"""Simple, deterministic *case-level* lexical baseline for SceneLock.

This is intentionally not an LLM and is not a full quality checker. It uses
only the screenplay and video-prompt text for prediction, then separately
uses expected labels to evaluate binary confirmed-issue detection.

Run:
    python evaluation/keyword_baseline.py

Outputs:
    evaluation/baseline_predictions.json
    evaluation/baseline_summary.json

These files are genuine deterministic baseline results, NOT Gemini results.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from validate_dataset import has_confirmed_issue, validate


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "sample_inputs" / "test_cases.json"
LABELS = ROOT / "evaluation" / "expected_labels.json"
PREDICTIONS = ROOT / "evaluation" / "baseline_predictions.json"
SUMMARY = ROOT / "evaluation" / "baseline_summary.json"

# Fixed a priori, not tuned to the 15 expected labels.
KEYWORD_RECALL_THRESHOLD = 0.50
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "as", "is", "are", "was",
    "were", "it", "its", "she", "he", "her", "his", "they", "their", "on",
    "at", "by", "from", "with", "into", "inside", "in", "for", "while",
    "then", "before", "after", "that", "this", "there", "when", "who",
    "which", "only", "beside", "toward", "through", "up", "out", "off",
    "has", "have", "had", "be", "been", "would", "could", "should",
}


def keywords(text: str) -> set[str]:
    """Return unique casefolded content words, with no semantic synonyms."""
    words = re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)
    return {w for w in words if len(w) >= 2 and w not in STOPWORDS}


def predict_case(case: dict) -> dict:
    """No use of expected labels, tags, shot intent, or case ID in judgment."""
    source = keywords(case["screenplay_text"])
    prompt = keywords(case["video_prompt"])
    matched = sorted(source & prompt)
    unmatched = sorted(source - prompt)
    recall = len(matched) / len(source) if source else 0.0
    return {
        "test_id": case["test_id"],
        "matched_keyword_count": len(matched),
        "source_keyword_count": len(source),
        "lexical_recall": round(recall, 4),
        "matched_keywords": matched,
        "unmatched_screenplay_keywords": unmatched,
        "predicted_has_confirmed_issue": recall < KEYWORD_RECALL_THRESHOLD,
        "decision_rule": f"Flag potential issue if raw token recall < {KEYWORD_RECALL_THRESHOLD:.2f}",
    }


def evaluate(predictions: list[dict], labels: list[dict]) -> dict:
    # Read ground truth only AFTER predictions are generated.
    ground_truth = {
        item["test_id"]: has_confirmed_issue(item["expected_facts"])
        for item in labels
    }
    tp = fp = tn = fn = 0
    errors = []
    for p in predictions:
        gold = ground_truth[p["test_id"]]
        predicted = p["predicted_has_confirmed_issue"]
        if predicted and gold:
            tp += 1
        elif predicted and not gold:
            fp += 1
            errors.append({"test_id": p["test_id"], "error": "false_positive"})
        elif not predicted and gold:
            fn += 1
            errors.append({"test_id": p["test_id"], "error": "false_negative"})
        else:
            tn += 1

    return {
        "evaluation_type": "actual_deterministic_keyword_baseline_only",
        "not_an_llm_result": True,
        "case_count": len(predictions),
        "gold_definition": "True if one or more High/Medium screenplay facts are Contradicted or Missing; Ambiguous by itself is not a confirmed issue.",
        "method": "Set overlap of unique lowercased source keywords found verbatim in the prompt; no synonym or scope reasoning.",
        "keyword_recall_threshold": KEYWORD_RECALL_THRESHOLD,
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "errors": errors,
        "limitations": [
            "Binary case-level issue flag only; cannot detect exact finding type or severity.",
            "Cannot distinguish contradiction from a missing detail.",
            "Does not use shot type or shot intent, so it may flag valid close-ups.",
            "Misses wrong colors/roles if enough other exact tokens overlap.",
            "Treats synonyms as different keywords; Hindi-English transliteration is unsupported.",
            "Threshold is fixed in advance and was not optimized on this dataset.",
        ],
    }


def main() -> None:
    consistency = validate()
    if consistency["error_count"]:
        raise SystemExit("Fix dataset validation errors before running baseline")
    inputs = json.loads(INPUTS.read_text(encoding="utf-8"))
    labels = json.loads(LABELS.read_text(encoding="utf-8"))

    predictions = [predict_case(c) for c in inputs["cases"]]
    summary = evaluate(predictions, labels["labels"])

    PREDICTIONS.write_text(
        json.dumps({
            "dataset_id": inputs["dataset_id"],
            "baseline": "keyword_overlap_v1",
            "not_an_llm_result": True,
            "predictions": predictions,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
