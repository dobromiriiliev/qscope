from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp


def entropy(values: np.ndarray, axis=None):
    values = np.asarray(values, dtype=float)
    positive = values > 0
    terms = np.zeros_like(values, dtype=float)
    terms[positive] = values[positive] * np.log(values[positive])
    return -np.sum(terms, axis=axis)


def weighted_quantile(values, weights, quantile: float) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights)
    cumulative /= cumulative[-1]
    index = int(np.searchsorted(cumulative, quantile, side="left"))
    index = min(index, len(values) - 1)
    return float(values[index])


@dataclass(frozen=True)
class Belief:
    hypotheses: tuple
    weights: np.ndarray

    @classmethod
    def uniform(cls, hypotheses):
        hypotheses = tuple(hypotheses)
        return cls(
            hypotheses,
            np.full(len(hypotheses), 1.0 / len(hypotheses), dtype=float),
        )

    @classmethod
    def location_uniform(cls, hypotheses):
        hypotheses = tuple(hypotheses)
        locations = tuple(dict.fromkeys(h.location for h in hypotheses))
        weights = np.zeros(len(hypotheses), dtype=float)

        for location in locations:
            indices = [h.id for h in hypotheses if h.location == location]
            mass = 1.0 / len(locations)
            weights[indices] = mass / len(indices)

        return cls(hypotheses, weights)

    @property
    def locations(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(h.location for h in self.hypotheses))

    def indices_for_location(self, location: str) -> np.ndarray:
        return np.array(
            [h.id for h in self.hypotheses if h.location == location],
            dtype=int,
        )

    def location_posterior(self) -> dict[str, float]:
        return {
            location: float(self.weights[self.indices_for_location(location)].sum())
            for location in self.locations
        }

    def top_location(self) -> tuple[str, float]:
        return max(self.location_posterior().items(), key=lambda item: item[1])

    def delta_mean(self, location: str) -> float:
        indices = self.indices_for_location(location)
        weights = self.weights[indices]
        weights = weights / weights.sum()
        values = np.array([self.hypotheses[i].delta for i in indices], dtype=float)
        return float(weights @ values)

    def credible_interval(
        self,
        location: str,
        level: float = 0.90,
    ) -> tuple[float, float]:
        indices = self.indices_for_location(location)
        weights = self.weights[indices]
        weights = weights / weights.sum()
        values = np.array([self.hypotheses[i].delta for i in indices], dtype=float)
        tail = (1.0 - level) / 2.0
        return (
            weighted_quantile(values, weights, tail),
            weighted_quantile(values, weights, 1.0 - tail),
        )

    def total_entropy(self) -> float:
        return float(entropy(self.weights))


def bayesian_update(belief: Belief, log_likelihood: np.ndarray) -> Belief:
    log_weights = np.log(np.clip(belief.weights, 1e-300, 1.0)) + log_likelihood
    log_weights -= logsumexp(log_weights)
    return Belief(belief.hypotheses, np.exp(log_weights))
