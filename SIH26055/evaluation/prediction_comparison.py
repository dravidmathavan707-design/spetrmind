"""Reproducible experiment comparing the baseline TemporalModel to the RF predictor."""

from __future__ import annotations

import json
from pathlib import Path

from sklearn.metrics import brier_score_loss, roc_auc_score

from environment.scenarios import SCENARIOS
from evaluation.metrics import compute_metrics
from evaluation.prediction_metrics import accuracy_score, f1_score, precision_score, recall_score
from prediction.rf_dataset import build_dataset
from prediction.rf_features import build_feature_row
from prediction.rf_predictor import RFPredictor
from prediction.temporal_model import TemporalModel
from receiver.receiver import Receiver


def _label_predictions(predictions, threshold=0.5):
    return [1 if value >= threshold else 0 for value in predictions]


def _evaluate_predictions(labels, baseline_predictions, rf_predictions):
    baseline_labels = _label_predictions(baseline_predictions)
    rf_labels = _label_predictions(rf_predictions)

    return {
        "baseline": {
            "accuracy": accuracy_score(labels, baseline_labels),
            "precision": precision_score(labels, baseline_labels),
            "recall": recall_score(labels, baseline_labels),
            "f1": f1_score(labels, baseline_labels),
            "roc_auc": roc_auc_score(labels, baseline_predictions),
            "brier_score": brier_score_loss(labels, baseline_predictions),
        },
        "rf_model": {
            "accuracy": accuracy_score(labels, rf_labels),
            "precision": precision_score(labels, rf_labels),
            "recall": recall_score(labels, rf_labels),
            "f1": f1_score(labels, rf_labels),
            "roc_auc": roc_auc_score(labels, rf_predictions),
            "brier_score": brier_score_loss(labels, rf_predictions),
        },
    }


def _simulate_scheduler_for_predictor(scenario_factory, predictor_name, num_bands=20, steps=40, horizon=3):
    """Run a simple probability-based scheduler for the same scenario and return scheduler metrics."""
    world = scenario_factory(num_bands=num_bands)
    receiver = Receiver()
    observations = []
    band_history = {band_id: [] for band_id in range(num_bands)}
    model = TemporalModel(num_bands=num_bands) if predictor_name == "baseline" else None
    rf_model = RFPredictor() if predictor_name == "rf_model" else None

    if predictor_name == "rf_model":
        training_rows = build_dataset(scenario_factory, num_bands=num_bands, steps=max(steps, 12), prediction_horizon=horizon)
        if training_rows:
            rf_model.fit(training_rows)

    for time in range(steps):
        world.current_time = time - 1
        world.step(dt=1)
        candidate_scores = {}

        for band_id in range(num_bands):
            band_history[band_id].append({
                "time": time,
                "band": band_id,
                "detected": bool(world.query_band(band_id)[0]),
                "signal_strength": float(world.query_band(band_id)[1] or 0.0),
            })

            if predictor_name == "baseline":
                model.update({
                    "time": time,
                    "band": band_id,
                    "detected": bool(world.query_band(band_id)[0]),
                    "signal_strength": float(world.query_band(band_id)[1] or 0.0),
                })
                score = model.predict(band_id, time + horizon)
            else:
                row = build_feature_row(
                    band_history[band_id],
                    current_time=time,
                    band_id=band_id,
                    prediction_horizon=horizon,
                )
                score = rf_model.predict([row])[0]
            candidate_scores[band_id] = score

        selected_band = max(range(num_bands), key=lambda band_id: (candidate_scores[band_id], -band_id))
        actual_active, actual_strength = world.query_band(selected_band)
        observation = receiver.scan(selected_band, world)
        observation["actual_active"] = actual_active
        observation["actual_signal_strength"] = actual_strength
        observations.append(observation)

    return compute_metrics(observations)


def run_prediction_comparison(
    scenarios=None,
    seeds=(0,),
    num_bands=20,
    steps=40,
    horizon=3,
    prediction_window=3,
    output_path="data/generated/prediction_comparison.json",
):
    """Run a reproducible prediction comparison between the temporal baseline and the RF model."""
    scenario_entries = scenarios or [
        ("stable", SCENARIOS["stable"]),
        ("bursty", SCENARIOS["bursty"]),
        ("periodic", SCENARIOS["periodic"]),
        ("frequency_agile", SCENARIOS["frequency_agile"]),
    ]

    report = {
        "config": {
            "num_bands": num_bands,
            "steps": steps,
            "horizon": horizon,
            "prediction_window": prediction_window,
            "seeds": list(seeds),
        },
        "results": [],
    }

    for scenario_name, scenario_factory in scenario_entries:
        for seed in seeds:
            rows = build_dataset(scenario_factory, num_bands=num_bands, steps=steps, prediction_horizon=horizon)
            labels = [int(row["future_activity"]) for row in rows]

            if not rows:
                continue

            train_end = max(1, int(len(rows) * 0.6))
            train_rows = rows[:train_end]
            test_rows = rows[train_end:]

            rf_model = RFPredictor()
            rf_model.fit(train_rows)
            rf_predictions = rf_model.predict(test_rows)

            baseline_predictions = []
            baseline_model = TemporalModel(num_bands=num_bands)
            for row in rows:
                baseline_model.update({
                    "time": row["time"],
                    "band": row["band_id"],
                    "detected": bool(row.get("actual_active", False)),
                    "signal_strength": float(row.get("actual_signal_strength") or 0.0),
                })
                baseline_predictions.append(baseline_model.predict(row["band_id"], row["time"] + horizon))

            test_labels = [int(row["future_activity"]) for row in test_rows]
            baseline_test_predictions = [
                baseline_model.predict(row["band_id"], row["time"] + horizon)
                for row in test_rows
            ]
            rf_test_predictions = rf_model.predict(test_rows)
            prediction_metrics = _evaluate_predictions(test_labels, baseline_test_predictions, rf_test_predictions)

            scheduler_results = {
                "baseline": _simulate_scheduler_for_predictor(scenario_factory, "baseline", num_bands=num_bands, steps=steps, horizon=horizon),
                "rf_model": _simulate_scheduler_for_predictor(scenario_factory, "rf_model", num_bands=num_bands, steps=steps, horizon=horizon),
            }

            scenario_result = {
                "scenario": scenario_name,
                "seed": seed,
                "prediction_metrics": prediction_metrics,
                "scheduler_metrics": scheduler_results,
                "samples": {
                    "train": len(train_rows),
                    "test": len(test_rows),
                },
            }
            report["results"].append(scenario_result)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def compare_models(baseline_predictions, rf_predictions, labels):
    """Backward-compatible wrapper for older callers."""
    return _evaluate_predictions(labels, baseline_predictions, rf_predictions)
