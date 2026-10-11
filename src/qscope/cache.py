from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import binom


@dataclass(frozen=True)
class PredictionCache:
    p_plus: np.ndarray

    @classmethod
    def build(cls, hypotheses, experiments, predictor):
        values = np.empty((len(hypotheses), len(experiments)), dtype=float)
        for hypothesis in hypotheses:
            for experiment in experiments:
                values[hypothesis.id, experiment.id] = predictor.p_plus(hypothesis.params, experiment)
        return cls(values)


class LikelihoodCache:
    def __init__(self, probabilities, logs):
        self._probabilities = probabilities
        self._logs = logs

    @classmethod
    def build(cls, predictions: PredictionCache, experiments):
        probabilities = []
        logs = []
        for experiment in experiments:
            counts = np.arange(experiment.shots + 1)
            p = predictions.p_plus[:, experiment.id][:, None]
            logpmf = binom.logpmf(counts[None, :], experiment.shots, p)
            probabilities.append(np.exp(logpmf))
            logs.append(logpmf)
        return cls(tuple(probabilities), tuple(logs))

    def probabilities(self, experiment_id: int) -> np.ndarray:
        return self._probabilities[experiment_id]

    def log_likelihood(self, experiment_id: int, plus_count: int) -> np.ndarray:
        return self._logs[experiment_id][:, plus_count]
