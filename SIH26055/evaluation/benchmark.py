
"""First benchmark: Fixed vs Random schedulers on identical RF scenarios."""

import statistics

from environment.rf_world import RFWorld
from environment.emitter import Emitter
from receiver.receiver import Receiver
from scheduler.fixed import FixedScheduler
from scheduler.random import RandomScheduler
from evaluation.metrics import compute_metrics


def build_scenario(num_bands=20, band_id=3, signal_strength=-60, start_time=10, duration=10):
    """Fresh RFWorld + emitter, built the same way every time (no shared mutable state)."""
    world = RFWorld(num_bands=num_bands)
    world.add_emitter(Emitter(band_id=band_id, signal_strength=signal_strength,
                               start_time=start_time, duration=duration))
    return world


def run_scheduler(scheduler, world, steps=100, receiver=None):
    """Advance the RF world and let the scheduler+receiver scan for `steps` steps."""
    receiver = receiver or Receiver()
    observations = []

    for t in range(steps):
        world.current_time = t - 1
        world.step(dt=1)
        band = scheduler.next_band()
        actual_active, actual_strength = world.query_band(band)
        obs = receiver.scan(band, world)
        obs["actual_active"] = actual_active
        obs["actual_signal_strength"] = actual_strength
        observations.append(obs)

    return observations


def run_fixed(num_bands=20, steps=100, scenario_kwargs=None):
    scenario_kwargs = scenario_kwargs or {}
    world = build_scenario(num_bands=num_bands, **scenario_kwargs)
    scheduler = FixedScheduler(num_bands=num_bands)
    observations = run_scheduler(scheduler, world, steps=steps)
    return compute_metrics(observations)


def run_random(num_bands=20, steps=100, seed=42, scenario_kwargs=None):
    scenario_kwargs = scenario_kwargs or {}
    world = build_scenario(num_bands=num_bands, **scenario_kwargs)
    scheduler = RandomScheduler(num_bands=num_bands, seed=seed)
    observations = run_scheduler(scheduler, world, steps=steps)
    return compute_metrics(observations)


def run_strategy(scheduler, world, steps=100, receiver=None):
    """Run any scheduler through the common evaluation pipeline."""
    return compute_metrics(run_scheduler(scheduler, world, steps, receiver))


def compare(num_bands=20, steps=100, seed=42, scenario_kwargs=None):
    fixed_result = run_fixed(num_bands=num_bands, steps=steps, scenario_kwargs=scenario_kwargs)
    random_result = run_random(num_bands=num_bands, steps=steps, seed=seed, scenario_kwargs=scenario_kwargs)

    print("=" * 40)
    print("       FIXED vs RANDOM")
    print("=" * 40)
    print(f"{'Metric':<20}{'Fixed':>10}{'Random':>10}")
    print("-" * 40)
    print(f"{'Total scans':<20}{fixed_result['total_scans']:>10}{random_result['total_scans']:>10}")
    print(f"{'Hits':<20}{fixed_result['hits']:>10}{random_result['hits']:>10}")
    print(f"{'Misses':<20}{fixed_result['misses']:>10}{random_result['misses']:>10}")
    print(f"{'Detection ratio':<20}{fixed_result['detection_rate']:>10.2f}{random_result['detection_rate']:>10.2f}")
    print(f"{'Pd':<20}{str(fixed_result['probability_of_detection']):>10}{str(random_result['probability_of_detection']):>10}")
    print(f"{'Pfa':<20}{str(fixed_result['false_alarm_probability']):>10}{str(random_result['false_alarm_probability']):>10}")
    print(f"{'First detection':<20}{str(fixed_result['first_detection_time']):>10}{str(random_result['first_detection_time']):>10}")

    return {"fixed": fixed_result, "random": random_result}


def repeat_trials(num_bands=20, steps=100, seeds=range(1, 101), scenario_kwargs=None):
    """Run Fixed once (deterministic) and Random across many seeds; summarize distributions."""
    fixed_result = run_fixed(num_bands=num_bands, steps=steps, scenario_kwargs=scenario_kwargs)

    random_results = [
        run_random(num_bands=num_bands, steps=steps, seed=seed, scenario_kwargs=scenario_kwargs)
        for seed in seeds
    ]

    def summarize(key):
        values = [r[key] for r in random_results]
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

    random_summary = {
        "detection_rate": summarize("detection_rate"),
        "hits": summarize("hits"),
    }

    return {
        "fixed": fixed_result,
        "random_trials": random_results,
        "random_summary": random_summary,
    }
