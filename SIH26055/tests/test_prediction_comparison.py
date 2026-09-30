from evaluation.prediction_comparison import run_prediction_comparison
from environment.scenarios import SCENARIOS


def test_run_prediction_comparison_produces_reproducible_results(tmp_path):
    output_path = tmp_path / "prediction_comparison.json"
    report = run_prediction_comparison(
        scenarios=[("stable", SCENARIOS["stable"])],
        seeds=(0,),
        num_bands=4,
        steps=12,
        horizon=2,
        output_path=str(output_path),
    )

    assert report["results"]
    assert output_path.exists()
    assert "prediction_metrics" in report["results"][0]
    assert "scheduler_metrics" in report["results"][0]
    assert "baseline" in report["results"][0]["scheduler_metrics"]
    assert "rf_model" in report["results"][0]["scheduler_metrics"]
