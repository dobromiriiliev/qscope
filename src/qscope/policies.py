from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Literal

import numpy as np

from .inference import ParticlePosterior, entropy, weighted_variance
from .types import Experiment

ActiveScore = Literal["variance", "information_gain"]


@dataclass
class PredictionCache:
    predictions: dict[tuple[str, float, str, int], np.ndarray] = field(default_factory=dict)

    def get(self, experiment: Experiment) -> np.ndarray | None:
        return self.predictions.get(experiment.key)

    def put(self, experiment: Experiment, values: np.ndarray) -> None:
        self.predictions[experiment.key] = np.asarray(values, dtype=float)

    def require(self, experiment: Experiment) -> np.ndarray:
        values = self.get(experiment)
        if values is None:
            raise KeyError(f"missing cached predictions for {experiment.label}")
        return values


def information_gain_score(posterior: ParticlePosterior, predictions: np.ndarray) -> float:
    """Expected one-shot information gain for a +/-1 measurement."""
    mu = np.clip(np.asarray(predictions, dtype=float), -1.0, 1.0)
    p_plus_model = np.clip((1.0 + mu) / 2.0, 1e-12, 1.0 - 1e-12)
    w = posterior.weights
    p_plus = float(np.dot(w, p_plus_model))
    p_minus = 1.0 - p_plus

    prior_h = entropy(w)
    expected_h = 0.0
    if p_plus > 1e-15:
        w_plus = w * p_plus_model / p_plus
        expected_h += p_plus * entropy(w_plus)
    if p_minus > 1e-15:
        w_minus = w * (1.0 - p_plus_model) / p_minus
        expected_h += p_minus * entropy(w_minus)
    return max(0.0, float(prior_h - expected_h))


def score_experiment(
    posterior: ParticlePosterior,
    predictions: np.ndarray,
    method: ActiveScore = "information_gain",
) -> float:
    if method == "variance":
        return weighted_variance(predictions, posterior.weights)
    if method == "information_gain":
        return information_gain_score(posterior, predictions)
    raise ValueError(f"unknown active score: {method}")


def choose_active_experiment(
    posterior: ParticlePosterior,
    experiments: list[Experiment],
    cache: PredictionCache,
    used_counts: dict[tuple[str, float, str, int], int] | None = None,
    *,
    score_method: ActiveScore = "information_gain",
    repeat_penalty: float = 0.35,
) -> tuple[Experiment, float]:
    if not experiments:
        raise ValueError("experiment space is empty")
    used_counts = used_counts or {}

    best: Experiment | None = None
    best_score = -np.inf
    for experiment in experiments:
        raw_score = score_experiment(posterior, cache.require(experiment), score_method)
        repeats = used_counts.get(experiment.key, 0)
        adjusted = raw_score / (1.0 + repeat_penalty * repeats)
        if adjusted > best_score:
            best = experiment
            best_score = adjusted

    assert best is not None
    return best, float(best_score)


def choose_random_experiment(experiments: list[Experiment], rng: random.Random) -> Experiment:
    if not experiments:
        raise ValueError("experiment space is empty")
    return rng.choice(experiments)


def choose_fixed_experiment(experiments: list[Experiment], step_index: int) -> Experiment:
    if not experiments:
        raise ValueError("experiment space is empty")
    return experiments[step_index % len(experiments)]
