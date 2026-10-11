from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qscope.backend import LocalQiskitBackend
from qscope.diagnosis import DiagnosisEngine, MismatchDetector, StoppingRule
from qscope.inference import Belief
from qscope.physics import apply_drift
from qscope.policies import FixedPolicy, HierarchicalInformationPolicy, RandomPolicy


@dataclass(frozen=True)
class BenchmarkScenario:
    location: str
    delta: float


def default_scenarios(cfg):
    deltas = (-0.275, 0.275)
    return [
        BenchmarkScenario(term, delta)
        for term in cfg.hypotheses.terms
        for delta in deltas
    ]


def result_metrics(result, true_location: str, true_delta: float):
    if result.delta_mean is None:
        delta_error = 0.0 if true_location == "NO_DRIFT" else abs(true_delta)
    else:
        delta_error = abs(result.delta_mean - true_delta)

    correct_location = result.location == true_location
    interval_covers = bool(
        result.delta_low is not None
        and result.delta_high is not None
        and result.delta_low <= true_delta <= result.delta_high
    )

    return {
        "status": result.status,
        "location_correct": correct_location,
        "delta_error": float(delta_error),
        "experiments_used": int(result.experiments_used),
        "shots_used": int(result.total_shots),
        "location_probability": float(result.location_probability),
        "interval_covers": interval_covers,
        "diagnosis_correct": bool(
            result.status == "SUCCESS"
            and correct_location
            and delta_error <= 0.075
        ),
    }


def _fixed_schedule(experiments, budget: int):
    count = min(len(experiments), max(1, budget))
    indices = np.linspace(0, len(experiments) - 1, count, dtype=int)
    return tuple(dict.fromkeys(int(i) for i in indices))


def _policy(name, cfg, seed, experiments):
    if name == "active":
        return HierarchicalInformationPolicy(cfg.policy.switch_confidence)
    if name == "random":
        return RandomPolicy(seed)
    if name == "fixed":
        return FixedPolicy(_fixed_schedule(experiments, cfg.stopping.max_experiments))
    raise ValueError(name)


def run_benchmark(
    cfg,
    nominal,
    hypotheses,
    experiments,
    predictions,
    likelihoods,
    trials: int,
    output,
):
    rows = []
    scenarios = default_scenarios(cfg)

    for trial in range(trials):
        for scenario_id, scenario in enumerate(scenarios):
            true_params = apply_drift(
                nominal,
                None if scenario.location == "NO_DRIFT" else scenario.location,
                scenario.delta,
            )
            measurement_seed = cfg.seed + 10000 * trial + 100 * scenario_id

            for policy_name in ("active", "random", "fixed"):
                engine = DiagnosisEngine(
                    hypotheses,
                    experiments,
                    predictions,
                    likelihoods,
                    LocalQiskitBackend(true_params),
                    _policy(policy_name, cfg, measurement_seed + 31, experiments),
                    Belief.location_uniform(hypotheses),
                    StoppingRule(cfg.stopping),
                    MismatchDetector(
                        cfg.mismatch.predictive_p_value,
                        cfg.mismatch.consecutive_failures,
                    ),
                    measurement_seed,
                )
                result = engine.run()
                row = {
                    "trial": trial,
                    "scenario": scenario_id,
                    "true_location": scenario.location,
                    "true_delta": scenario.delta,
                    "policy": policy_name,
                }
                row.update(
                    result_metrics(
                        result,
                        scenario.location,
                        scenario.delta,
                    )
                )
                rows.append(row)

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return rows


def summarize(rows):
    summary = {}

    for policy in ("active", "random", "fixed"):
        selected = [row for row in rows if row["policy"] == policy]
        summary[policy] = {
            "n": len(selected),
            "location_accuracy": float(
                np.mean([row["location_correct"] for row in selected])
            ),
            "mean_delta_error": float(
                np.mean([row["delta_error"] for row in selected])
            ),
            "mean_experiments": float(
                np.mean([row["experiments_used"] for row in selected])
            ),
            "status_success_rate": float(
                np.mean([row["status"] == "SUCCESS" for row in selected])
            ),
            "diagnosis_accuracy": float(
                np.mean([row["diagnosis_correct"] for row in selected])
            ),
            "coverage_90": float(
                np.mean([row["interval_covers"] for row in selected])
            ),
        }

    return summary
