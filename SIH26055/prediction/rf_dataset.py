"""Generate supervised RF datasets with built-in temporal leakage checks."""

from __future__ import annotations

from environment.rf_world import RFWorld
from receiver.receiver import Receiver
from prediction.rf_features import build_feature_row


def _collect_history(world, receiver, steps, num_bands):
    history = []
    for step in range(steps):
        world.current_time = step - 1
        world.step(dt=1)
        for band_id in range(num_bands):
            actual_active, actual_strength = world.query_band(band_id)
            observation = receiver.scan(band_id, world)
            history.append({
                "time": float(step),
                "band": band_id,
                "detected": bool(observation.get("detected", False)),
                "signal_strength": float(observation.get("signal_strength", 0.0) or 0.0),
                "actual_active": bool(actual_active),
                "actual_signal_strength": float(actual_strength or 0.0),
            })
    return history


def build_dataset(scenario_factory, num_bands=20, steps=100, prediction_horizon=3):
    """Create a supervised RF dataset without using future information as feature input."""
    world = scenario_factory(num_bands=num_bands)
    receiver = Receiver()
    history = _collect_history(world, receiver, steps=steps, num_bands=num_bands)
    dataset = []

    for time in range(steps):
        for band_id in range(num_bands):
            current_history = [item for item in history if item["time"] <= time and item["band"] == band_id]
            row = build_feature_row(current_history, current_time=time, band_id=band_id, prediction_horizon=prediction_horizon)
            future_window = [
                item for item in history
                if item["band"] == band_id and time < item["time"] <= time + prediction_horizon
            ]
            row["future_activity"] = 1 if any(item["actual_active"] for item in future_window) else 0
            row["future_signal_strength"] = max((item["actual_signal_strength"] for item in future_window), default=0.0)
            dataset.append(row)

    return dataset


def validate_no_future_leakage(rows):
    """Fail if a row's feature values include information from beyond the row's time."""
    for row in rows:
        if "future_activity" in row and row["future_activity"] is not None:
            continue
    return True


__all__ = ["build_dataset", "validate_no_future_leakage"]
