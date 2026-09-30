from environment.scenarios import stable
from prediction.rf_dataset import build_dataset
from prediction.rf_predictor import RFPredictor


def test_rf_predictor_trains_and_predicts():
    rows = build_dataset(stable, num_bands=4, steps=12, prediction_horizon=2)
    assert rows

    predictor = RFPredictor()
    predictor.fit(rows[:50])
    probabilities = predictor.predict(rows[:5])

    assert len(probabilities) == 5
    assert all(0.0 <= p <= 1.0 for p in probabilities)
