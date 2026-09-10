"""Unseen-environment evaluation for Fixed, Random, and integrated Smart scans."""

from evaluation.benchmark import run_strategy
from environment.scenarios import SCENARIOS
from main import run_cognitive_loop
from scheduler.fixed import FixedScheduler
from scheduler.random import RandomScheduler


DEVELOPMENT_SCENARIOS = ("stable", "bursty")
UNSEEN_SCENARIOS = (
    "periodic",
    "frequency_agile",
    "multiple_emitters",
    "weak",
    "noisy",
    "changing",
)


def _scenario_factory(name):
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario: {name}")
    return lambda num_bands=20: SCENARIOS[name](num_bands=num_bands)


def _validate_split():
    overlap = set(DEVELOPMENT_SCENARIOS) & set(UNSEEN_SCENARIOS)
    if overlap:
        raise ValueError(f"development and unseen scenarios overlap: {sorted(overlap)}")


def evaluate_unseen(num_bands=20, steps=100, random_seed=42,
                    scenario_names=UNSEEN_SCENARIOS):
    """Evaluate without fitting/tuning; each strategy receives a fresh same scenario."""
    _validate_split()
    unknown = set(scenario_names) - set(SCENARIOS)
    if unknown:
        raise ValueError(f"unknown scenarios: {sorted(unknown)}")
    if num_bands <= 0 or steps < 0:
        raise ValueError("num_bands must be > 0 and steps must be >= 0")

    results = {}
    for scenario_name in scenario_names:
        factory = _scenario_factory(scenario_name)
        fixed_world = factory(num_bands)
        random_world = factory(num_bands)
        results[scenario_name] = {
            "fixed": run_strategy(
                FixedScheduler(num_bands), fixed_world, steps=steps
            ),
            "random": run_strategy(
                RandomScheduler(num_bands, seed=random_seed), random_world, steps=steps
            ),
            "smart": run_cognitive_loop(
            num_bands=num_bands, steps=steps, scenario_factory=factory
            )["metrics"],
        }

    return {
        "development_scenarios": DEVELOPMENT_SCENARIOS,
        "unseen_scenarios": tuple(scenario_names),
        "results": results,
    }


def summarize_unseen(evaluation):
    """Average always-defined scan metrics across held-out scenarios."""
    scenario_results = evaluation["results"]
    summary = {}
    for strategy in ("fixed", "random", "smart"):
        values = [scenario[strategy] for scenario in scenario_results.values()]
        summary[strategy] = {
            "detection_rate": sum(item["detection_rate"] for item in values) / len(values),
            "total_scans": sum(item["total_scans"] for item in values),
            "hits": sum(item["hits"] for item in values),
            "misses": sum(item["misses"] for item in values),
        }
    return summary
