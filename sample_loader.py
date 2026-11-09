"""Small, read-only catalog of original synthetic SceneLock demo inputs.

Only user-facing inputs are exposed; ground-truth labels and evaluation
metadata are never sent to the Gemini adapter.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from schemas import AnalysisInput


DEMO_LABELS = {
    "T01": "Costume contradiction",
    "T03": "Handbag / purse synonym",
    "T05": "Missing critical action",
    "T06": "Reaction close-up scope",
    "T09": "Uncertain character identity",
    "T15": "Hindi-English dialogue",
}

INPUT_FIELDS = (
    "screenplay_text", "video_prompt", "shot_type", "shot_intent",
    "episode_id", "scene_id", "shot_id",
)


@lru_cache(maxsize=1)
def demo_samples() -> dict[str, dict[str, str]]:
    """Return display-label -> validated *input fields only* for six demos."""
    path = Path(__file__).resolve().parent / "sample_inputs" / "test_cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    indexed = {case["test_id"]: case for case in data["cases"]}
    catalog: dict[str, dict[str, str]] = {}
    for test_id, description in DEMO_LABELS.items():
        if test_id not in indexed:
            raise ValueError(f"Bundled demo {test_id} is missing from the dataset.")
        inputs = {name: indexed[test_id].get(name) or "" for name in INPUT_FIELDS}
        AnalysisInput.model_validate(inputs)
        catalog[f"{test_id} · {description}"] = inputs
    return catalog
