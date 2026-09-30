import pytest

from environment.scenarios import stable
from prediction.rf_dataset import build_dataset, validate_no_future_leakage
from prediction.rf_features import build_feature_row


def test_build_feature_row_rejects_future_history():
    with pytest.raises(ValueError, match="future"):
        build_feature_row(
            [
                {"time": 0, "band": 1, "detected": False, "signal_strength": 0.0},
                {"time": 5, "band": 1, "detected": True, "signal_strength": 0.9},
            ],
            current_time=2,
            band_id=1,
        )


def test_dataset_builds_future_activity_labels_without_leakage():
    rows = build_dataset(stable, num_bands=4, steps=12, prediction_horizon=2)

    assert rows
    assert all("future_activity" in row for row in rows)
    assert all("time" in row for row in rows)
    assert all("band_id" in row for row in rows)

    validate_no_future_leakage(rows)

    assert rows[0]["time"] >= 0
