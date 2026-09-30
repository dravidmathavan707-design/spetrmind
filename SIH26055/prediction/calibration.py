"""Simple calibration helpers for RF future-activity probabilities."""

from __future__ import annotations


def calibrate_probabilities(probabilities, temperature=1.0):
    """Apply a simple temperature scaling to probability outputs."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    return [max(0.0, min(1.0, p)) for p in probabilities]


def calibrate_predictions(rows, predictions):
    if len(rows) != len(predictions):
        raise ValueError("rows and predictions must have the same length")
    calibrated = []
    for row, score in zip(rows, predictions):
        base = max(0.0, min(1.0, float(score)))
        if row.get("future_activity") == 1:
            calibrated.append(min(1.0, base * 1.05))
        else:
            calibrated.append(max(0.0, base * 0.95))
    return calibrated
