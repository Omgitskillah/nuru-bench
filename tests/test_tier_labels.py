"""The generic cheapest-passing-tier report remains useful without a learned classifier."""
import importlib
import runpy
from pathlib import Path
from types import SimpleNamespace


def test_tier_labels_require_two_passes_and_preserve_missing_expert_state(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1] / "decision_layer"
    monkeypatch.syspath_prepend(str(path))
    tiers = importlib.import_module("tier_labels")
    records = [
        {"test": 1, "tier": "off", "points": 5, "model_seconds": 2},
        {"test": 1, "tier": "off", "points": 1, "model_seconds": None},
        {"test": 1, "tier": "true", "points": 5, "model_seconds": 5},
        {"test": 1, "tier": "true", "points": 4, "model_seconds": 6},
        {"test": 2, "tier": "low", "points": 1, "model_seconds": None},
        {"test": 3, "tier": "expert", "points": 1, "model_seconds": None},
    ]
    scorer = importlib.import_module("score_runs")
    monkeypatch.setattr(scorer, "score", lambda r: (r["points"], [("correct", r["points"] >= 4)]))
    monkeypatch.setattr(tiers, "score", scorer.score)
    monkeypatch.setattr(tiers, "load_results", lambda batch: records)
    assert tiers.load(tmp_path) == records
    result = tiers.table(records)
    assert result[1]["high"]["passes"] == 2 and result[1]["high"]["mean_model_seconds"] == 5.5
    assert tiers.labels(result, ("off", "low", "high", "expert")) == {1: "high", 2: "expert", 3: "none"}
    assert tiers.tier_of("off") == "off"
    common = importlib.import_module("common")
    saved = []
    monkeypatch.setattr(scorer, "load_results", lambda batch: records)
    monkeypatch.setattr(common, "save", lambda name, data: saved.append((name, data)) or tmp_path / "out.json")
    monkeypatch.setattr("sys.argv", ["tier_labels", str(tmp_path)])
    runpy.run_path(str(path / "tier_labels.py"), run_name="__main__")
    assert saved[0][0] == "tier_labels" and saved[0][1]["labels"][1] == "high"
