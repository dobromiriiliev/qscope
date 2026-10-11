from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from qscope.inference import entropy


@dataclass(frozen=True)
class PolicyDecision:
    experiment_id: int
    score: float
    mode: str
    explanation: str


def _membership(belief) -> np.ndarray:
    matrix = np.zeros(
        (len(belief.locations), len(belief.hypotheses)),
        dtype=float,
    )

    for row, location in enumerate(belief.locations):
        matrix[row, belief.indices_for_location(location)] = 1.0

    return matrix


class HierarchicalInformationPolicy:
    def __init__(self, switch_confidence: float):
        self.switch_confidence = switch_confidence

    def _location_scores(self, belief, likelihoods, experiments):
        location_posterior = belief.location_posterior()
        current = np.array(
            [location_posterior[x] for x in belief.locations],
            dtype=float,
        )
        current_entropy = entropy(current)
        membership = _membership(belief)
        scores = np.zeros(len(experiments), dtype=float)

        for experiment in experiments:
            pmf = likelihoods.probabilities(experiment.id)
            predictive = belief.weights @ pmf
            joint = belief.weights[:, None] * pmf
            posterior = np.divide(
                joint,
                predictive[None, :],
                out=np.zeros_like(joint),
                where=predictive[None, :] > 0,
            )
            location_given_count = membership @ posterior
            expected_entropy = float(
                predictive @ entropy(location_given_count, axis=0)
            )
            scores[experiment.id] = current_entropy - expected_entropy

        return scores

    def _delta_scores(self, belief, location, likelihoods, experiments):
        indices = belief.indices_for_location(location)
        conditional = belief.weights[indices]
        conditional = conditional / conditional.sum()
        current_entropy = entropy(conditional)
        scores = np.zeros(len(experiments), dtype=float)

        for experiment in experiments:
            pmf = likelihoods.probabilities(experiment.id)[indices, :]
            predictive = conditional @ pmf
            joint = conditional[:, None] * pmf
            posterior = np.divide(
                joint,
                predictive[None, :],
                out=np.zeros_like(joint),
                where=predictive[None, :] > 0,
            )
            expected_entropy = float(predictive @ entropy(posterior, axis=0))
            scores[experiment.id] = current_entropy - expected_entropy

        return scores

    def _location_expectation(self, belief, location, experiment_id, predictions):
        indices = belief.indices_for_location(location)
        weights = belief.weights[indices]
        total = float(weights.sum())

        if total <= 0:
            return None

        weights = weights / total
        p = float(weights @ predictions.p_plus[indices, experiment_id])
        return 2.0 * p - 1.0

    def _explanation(self, belief, experiment, predictions):
        ranked = sorted(
            belief.location_posterior().items(),
            key=lambda item: item[1],
            reverse=True,
        )

        values = []
        for location, _ in ranked:
            expectation = self._location_expectation(
                belief,
                location,
                experiment.id,
                predictions,
            )
            if expectation is not None:
                values.append((location, expectation))
            if len(values) == 2:
                break

        if len(values) < 2:
            return (
                f"Selected {experiment.observable} at "
                f"t={experiment.evolution_time:g}."
            )

        gap = abs(values[0][1] - values[1][1])
        return (
            f"Selected {experiment.observable} at t={experiment.evolution_time:g}; "
            f"the two leading location hypotheses differ by {gap:.3f} "
            f"in predicted expectation."
        )

    def select(self, belief, experiments, predictions, likelihoods):
        location, confidence = belief.top_location()

        if location != "NO_DRIFT" and confidence >= self.switch_confidence:
            scores = self._delta_scores(
                belief,
                location,
                likelihoods,
                experiments,
            )
            mode = "CALIBRATE"
        else:
            scores = self._location_scores(
                belief,
                likelihoods,
                experiments,
            )
            mode = "LOCALIZE"

        experiment_id = int(np.argmax(scores))
        experiment = experiments[experiment_id]

        return PolicyDecision(
            experiment_id,
            float(scores[experiment_id]),
            mode,
            self._explanation(belief, experiment, predictions),
        )


class RandomPolicy:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)

    def select(self, belief, experiments, predictions, likelihoods):
        experiment_id = int(self.rng.integers(0, len(experiments)))
        experiment = experiments[experiment_id]
        return PolicyDecision(
            experiment_id,
            0.0,
            "RANDOM",
            (
                f"Selected {experiment.observable} at "
                f"t={experiment.evolution_time:g} randomly."
            ),
        )


class FixedPolicy:
    def __init__(self, experiment_ids=None):
        self.experiment_ids = (
            None if experiment_ids is None else tuple(experiment_ids)
        )
        self.position = 0

    def select(self, belief, experiments, predictions, likelihoods):
        schedule = self.experiment_ids or tuple(range(len(experiments)))
        experiment_id = int(schedule[self.position % len(schedule)])
        self.position += 1
        experiment = experiments[experiment_id]
        return PolicyDecision(
            experiment_id,
            0.0,
            "FIXED",
            (
                f"Selected {experiment.observable} at "
                f"t={experiment.evolution_time:g} from the fixed schedule."
            ),
        )
