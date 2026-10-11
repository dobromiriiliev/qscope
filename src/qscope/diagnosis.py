from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from qscope.inference import bayesian_update


class MismatchDetector:
    def __init__(self, threshold: float, consecutive_failures: int):
        self.threshold = threshold
        self.consecutive_failures = consecutive_failures
        self.failures = 0

    def evaluate(self, belief, likelihoods, experiment_id: int, observed_count: int) -> float:
        predictive = belief.weights @ likelihoods.probabilities(experiment_id)
        observed_probability = predictive[observed_count]
        p_value = float(np.sum(predictive[predictive <= observed_probability + 1e-15]))
        self.failures = self.failures + 1 if p_value < self.threshold else 0
        return p_value

    @property
    def triggered(self) -> bool:
        return self.failures >= self.consecutive_failures


class StoppingRule:
    def __init__(self, cfg):
        self.cfg = cfg

    def check(self, belief, experiments_used: int, mismatch_triggered: bool):
        if mismatch_triggered:
            return "MODEL_MISMATCH"
        location, probability = belief.top_location()
        if location == "NO_DRIFT" and probability >= self.cfg.location_confidence:
            return "SUCCESS"
        if location != "NO_DRIFT" and probability >= self.cfg.location_confidence:
            low, high = belief.credible_interval(location, 0.90)
            if high - low <= self.cfg.credible_interval_width:
                return "SUCCESS"
        if experiments_used >= self.cfg.max_experiments:
            return "MAX_BUDGET"
        return None


@dataclass(frozen=True)
class StepResult:
    step: int
    mode: str
    experiment_id: int
    initial_state: str
    evolution_time: float
    observable: str
    score: float
    plus_count: int
    shots: int
    expectation: float
    top_location: str
    top_location_probability: float
    delta_mean: float | None
    delta_low: float | None
    delta_high: float | None
    posterior_entropy: float
    predictive_p_value: float
    explanation: str


@dataclass(frozen=True)
class DiagnosisResult:
    status: str
    location: str
    location_probability: float
    delta_mean: float | None
    delta_low: float | None
    delta_high: float | None
    experiments_used: int
    total_shots: int
    history: tuple[StepResult, ...]

    def to_dict(self):
        value = asdict(self)
        value["history"] = [asdict(step) for step in self.history]
        return value


class DiagnosisEngine:
    def __init__(
        self,
        hypotheses,
        experiments,
        predictions,
        likelihoods,
        backend,
        policy,
        belief,
        stopping_rule,
        mismatch_detector,
        seed: int,
    ):
        self.hypotheses = hypotheses
        self.experiments = experiments
        self.predictions = predictions
        self.likelihoods = likelihoods
        self.backend = backend
        self.policy = policy
        self.belief = belief
        self.stopping_rule = stopping_rule
        self.mismatch_detector = mismatch_detector
        self.seed = seed

    def run(self):
        history = []
        status = self.stopping_rule.check(self.belief, 0, False)
        while status is None:
            step = len(history) + 1
            decision = self.policy.select(self.belief, self.experiments, self.predictions, self.likelihoods)
            experiment = self.experiments[decision.experiment_id]
            observation = self.backend.run(experiment, self.seed + step)
            predictive_p = self.mismatch_detector.evaluate(
                self.belief,
                self.likelihoods,
                experiment.id,
                observation.plus_count,
            )
            self.belief = bayesian_update(
                self.belief,
                self.likelihoods.log_likelihood(experiment.id, observation.plus_count),
            )
            location, probability = self.belief.top_location()
            if location == "NO_DRIFT":
                delta_mean = delta_low = delta_high = None
            else:
                delta_mean = self.belief.delta_mean(location)
                delta_low, delta_high = self.belief.credible_interval(location, 0.90)
            history.append(
                StepResult(
                    step=step,
                    mode=decision.mode,
                    experiment_id=experiment.id,
                    initial_state=experiment.initial_state,
                    evolution_time=experiment.evolution_time,
                    observable=experiment.observable,
                    score=decision.score,
                    plus_count=observation.plus_count,
                    shots=observation.shots,
                    expectation=observation.expectation,
                    top_location=location,
                    top_location_probability=probability,
                    delta_mean=delta_mean,
                    delta_low=delta_low,
                    delta_high=delta_high,
                    posterior_entropy=self.belief.total_entropy(),
                    predictive_p_value=predictive_p,
                    explanation=decision.explanation,
                )
            )
            status = self.stopping_rule.check(self.belief, len(history), self.mismatch_detector.triggered)
        location, probability = self.belief.top_location()
        if location == "NO_DRIFT":
            delta_mean = delta_low = delta_high = None
        else:
            delta_mean = self.belief.delta_mean(location)
            delta_low, delta_high = self.belief.credible_interval(location, 0.90)
        return DiagnosisResult(
            status=status,
            location=location,
            location_probability=probability,
            delta_mean=delta_mean,
            delta_low=delta_low,
            delta_high=delta_high,
            experiments_used=len(history),
            total_shots=sum(item.shots for item in history),
            history=tuple(history),
        )
