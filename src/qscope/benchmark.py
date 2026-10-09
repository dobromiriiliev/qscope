from __future__ import annotations

from dataclasses import asdict

import numpy as np

from .diagnosis import precompute_predictions, run_diagnosis
from .hamiltonian import TFIMParams
from .inference import ParticlePosterior
from .types import Experiment


def benchmark_strategies(
    hidden: TFIMParams,
    nominal: TFIMParams,
    base_posterior: ParticlePosterior,
    experiments: list[Experiment],
    max_steps: int,
    trials: int,
    seed: int = 0,
    strategies: tuple[str, ...] = ("active", "random", "fixed"),
    active_score: str = "information_gain",
    repeat_penalty: float = 0.35,
) -> list[dict]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    cache = precompute_predictions(base_posterior, experiments)
    rows: list[dict] = []

    for strategy in strategies:
        for trial in range(trials):
            posterior = base_posterior.clone()
            result = run_diagnosis(
                hidden=hidden,
                nominal=nominal,
                posterior=posterior,
                experiments=experiments,
                max_steps=max_steps,
                strategy=strategy,  # type: ignore[arg-type]
                seed=seed + 1000 * trial,
                cache=cache,
                active_score=active_score,  # type: ignore[arg-type]
                repeat_penalty=repeat_penalty,
                stop_map_confidence=None,
            )
            for step in result.steps:
                row = asdict(step)
                row["trial"] = trial
                rows.append(row)
    return rows


def summarize_by_step(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    summary: list[dict] = []
    strategies = sorted({str(row["strategy"]) for row in rows})
    for strategy in strategies:
        strategy_rows = [r for r in rows if r["strategy"] == strategy]
        for step in sorted({int(r["step"]) for r in strategy_rows}):
            subset = [r for r in strategy_rows if int(r["step"]) == step]
            errors = np.asarray([float(r["relative_error"]) for r in subset], dtype=float)
            correct = np.asarray([bool(r["correct_drift_location"]) for r in subset], dtype=float)
            summary.append(
                {
                    "strategy": strategy,
                    "step": step,
                    "mean_relative_error": float(np.mean(errors)),
                    "std_relative_error": float(np.std(errors)),
                    "drift_location_accuracy": float(np.mean(correct)),
                    "trials": len(subset),
                }
            )
    return summary


def first_step_below_target(rows: list[dict], target_error: float) -> list[dict]:
    """Return one row per strategy/trial with first step reaching target, or None."""
    out: list[dict] = []
    keys = sorted({(str(r["strategy"]), int(r["trial"])) for r in rows})
    for strategy, trial in keys:
        trial_rows = sorted(
            [r for r in rows if r["strategy"] == strategy and int(r["trial"]) == trial],
            key=lambda r: int(r["step"]),
        )
        reached = next((r for r in trial_rows if float(r["relative_error"]) <= target_error), None)
        out.append(
            {
                "strategy": strategy,
                "trial": trial,
                "first_step_below_target": None if reached is None else int(reached["step"]),
                "reached_target": reached is not None,
            }
        )
    return out


def benchmark_headline(rows: list[dict], target_error: float) -> dict:
    hits = first_step_below_target(rows, target_error)
    result: dict[str, dict] = {}
    for strategy in sorted({h["strategy"] for h in hits}):
        subset = [h for h in hits if h["strategy"] == strategy]
        reached_steps = [h["first_step_below_target"] for h in subset if h["reached_target"]]
        result[strategy] = {
            "success_rate": float(np.mean([h["reached_target"] for h in subset])),
            "median_steps_when_successful": (
                None if not reached_steps else float(np.median(reached_steps))
            ),
            "target_relative_error": target_error,
        }
    return result
