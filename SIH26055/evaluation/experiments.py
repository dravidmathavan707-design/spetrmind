"""Repeatable multi-strategy experiments on identical scenario definitions."""

import statistics

from evaluation.benchmark import build_scenario, run_scheduler
from evaluation.metrics import compute_metrics
from receiver.receiver import Receiver


def run_trial(scheduler_factory, scenario_factory=build_scenario, steps=100,
			  receiver_factory=Receiver):
	"""Build fresh world, scheduler, and receiver for one fair trial."""
	world = scenario_factory()
	scheduler = scheduler_factory()
	observations = run_scheduler(
		scheduler, world, steps=steps, receiver=receiver_factory()
	)
	return compute_metrics(observations)


def compare_strategies(strategy_factories, scenario_factory=build_scenario,
					   steps=100):
	"""Run named scheduler factories against independently fresh identical worlds."""
	return {
		name: run_trial(factory, scenario_factory, steps)
		for name, factory in strategy_factories.items()
	}


def repeat_strategy_trials(strategy_factories, scenario_factory=build_scenario,
						   steps=100, trials=10):
	"""Return per-trial results and mean/stdev for core evaluation metrics."""
	trial_results = [
		compare_strategies(strategy_factories, scenario_factory, steps)
		for _ in range(trials)
	]
	summaries = {}
	for name in strategy_factories:
		summaries[name] = {}
		for metric in ("probability_of_detection", "false_alarm_probability",
					   "average_intercept_rate", "average_reward_cost"):
			values = [
				result[name][metric]
				for result in trial_results
				if result[name][metric] is not None
			]
			summaries[name][metric] = {
				"mean": statistics.mean(values) if values else None,
				"stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
			}
	return {"trials": trial_results, "summaries": summaries}
