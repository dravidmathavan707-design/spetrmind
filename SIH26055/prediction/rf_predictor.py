"""XGBoost-based RF future activity predictor with fallback to a calibrated sklearn model."""

from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier


class RFPredictor:
    def __init__(self, feature_columns=None):
        self.feature_columns = feature_columns or [
            "recent_hit_rate_3",
            "recent_hit_rate_5",
            "recent_hit_rate_10",
            "recent_hit_rate_20",
            "recent_miss_rate_5",
            "total_hits",
            "total_misses",
            "time_since_last_hit",
            "time_since_last_scan",
            "mean_signal_strength",
            "recent_signal_strength",
            "signal_strength_trend",
            "activity_probability",
            "estimated_period",
            "periodicity_confidence",
            "recent_activity_trend",
            "drift_score",
        ]
        self.model = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.08, max_iter=200, random_state=0)

    def fit(self, rows):
        X = [[row[col] for col in self.feature_columns] for row in rows]
        y = [int(row["future_activity"]) for row in rows]
        self.model.fit(X, y)
        return self

    def predict_proba(self, rows):
        X = [[row[col] for col in self.feature_columns] for row in rows]
        return self.model.predict_proba(X)

    def predict(self, rows):
        proba = self.predict_proba(rows)
        return [float(item[1]) for item in proba]
