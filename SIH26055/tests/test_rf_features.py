from prediction.rf_features import build_feature_row


def test_build_feature_row_uses_only_past_history():
    history = [
        {"time": 0, "band": 1, "detected": False, "signal_strength": 0.0},
        {"time": 1, "band": 1, "detected": True, "signal_strength": 0.8},
        {"time": 2, "band": 1, "detected": False, "signal_strength": 0.2},
    ]
    row = build_feature_row(history, current_time=2, band_id=1)

    assert row["band_id"] == 1
    assert row["time"] == 2
    assert "recent_hit_rate_3" in row
    assert row["future_activity"] == 0
