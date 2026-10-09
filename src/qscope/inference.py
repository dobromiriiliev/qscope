from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .hamiltonian import TFIMParams
from .types import Experiment, MeasurementResult

Predictor = Callable[[TFIMParams, Experiment], float]


def make_single_drift_particles(
    nominal: TFIMParams,
    parameter_indices: list[int],
    low: float,
    high: float,
    values_per_parameter: int,
) -> np.ndarray:
    """Create a grid prior where exactly one selected parameter may drift."""
    if values_per_parameter < 2:
        raise ValueError("values_per_parameter must be at least 2")
    if low >= high:
        raise ValueError("drift_low must be less than drift_high")
    base = nominal.as_vector()
    if not parameter_indices:
        raise ValueError("parameter_indices cannot be empty")
    if any(i < 0 or i >= len(base) for i in parameter_indices):
        raise ValueError("prior parameter index out of range")

    values = np.linspace(low, high, values_per_parameter)
    particles: list[np.ndarray] = []
    for index in parameter_indices:
        for value in values:
            candidate = base.copy()
            candidate[index] = value
            particles.append(candidate)

    # Avoid duplicate nominal particles when multiple drift axes cross at nominal.
    stacked = np.stack(particles)
    unique = np.unique(np.round(stacked, decimals=12), axis=0)
    return unique.astype(float)


def entropy(weights: np.ndarray) -> float:
    w = np.asarray(weights, dtype=float)
    w = w[w > 0]
    return float(-np.sum(w * np.log(w)))


@dataclass
class ParticlePosterior:
    particles: np.ndarray
    weights: np.ndarray
    num_qubits: int

    @classmethod
    def uniform(cls, particles: np.ndarray, num_qubits: int) -> "ParticlePosterior":
        particles = np.asarray(particles, dtype=float)
        if particles.ndim != 2 or len(particles) == 0:
            raise ValueError("particles must be a non-empty 2D array")
        weights = np.full(len(particles), 1.0 / len(particles), dtype=float)
        return cls(particles=particles, weights=weights, num_qubits=num_qubits)

    def clone(self) -> "ParticlePosterior":
        return ParticlePosterior(self.particles.copy(), self.weights.copy(), self.num_qubits)

    def normalize(self) -> None:
        total = float(np.sum(self.weights))
        if not np.isfinite(total) or total <= 0:
            raise RuntimeError("posterior normalization failed")
        self.weights = self.weights / total

    def mean_vector(self) -> np.ndarray:
        return np.average(self.particles, axis=0, weights=self.weights)

    def std_vector(self) -> np.ndarray:
        mean = self.mean_vector()
        variance = np.average(np.square(self.particles - mean), axis=0, weights=self.weights)
        return np.sqrt(np.maximum(variance, 0.0))

    def map_vector(self) -> np.ndarray:
        return self.particles[int(np.argmax(self.weights))].copy()

    def map_confidence(self) -> float:
        return float(np.max(self.weights))

    def effective_sample_size(self) -> float:
        return float(1.0 / np.sum(np.square(self.weights)))

    def entropy(self) -> float:
        return entropy(self.weights)

    def update_from_predictions(self, predictions: np.ndarray, result: MeasurementResult) -> None:
        """Bayesian update for repeated +/-1 Pauli measurements."""
        result.validate()
        mu = np.clip(np.asarray(predictions, dtype=float), -1.0, 1.0)
        if mu.shape != self.weights.shape:
            raise ValueError("predictions must have one entry per particle")
        p_plus = np.clip((1.0 + mu) / 2.0, 1e-12, 1.0 - 1e-12)
        log_likelihood = (
            result.plus_count * np.log(p_plus)
            + result.minus_count * np.log1p(-p_plus)
        )
        log_weights = np.log(np.clip(self.weights, 1e-300, None)) + log_likelihood
        log_weights -= np.max(log_weights)
        self.weights = np.exp(log_weights)
        self.normalize()


def prediction_vector(
    particles: np.ndarray,
    num_qubits: int,
    experiment: Experiment,
    predictor: Predictor,
) -> np.ndarray:
    return np.asarray(
        [predictor(TFIMParams.from_vector(v, num_qubits), experiment) for v in particles],
        dtype=float,
    )


def weighted_variance(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mean = float(np.average(values, weights=weights))
    return float(np.average(np.square(values - mean), weights=weights))
