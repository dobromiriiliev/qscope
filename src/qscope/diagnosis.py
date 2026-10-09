from __future__ import annotations

from dataclasses import asdict, dataclass
import random
from typing import Literal

from .hamiltonian import TFIMParams
from .inference import ParticlePosterior, prediction_vector
from .metrics import (
    detected_drift_index,
    drift_location_correct,
    relative_parameter_error,
)
from .policies import (
    ActiveScore,
    PredictionCache,
    choose_active_experiment,
    choose_fixed_experiment,
    choose_random_experiment,
)
from .simulator import exact_expectation, run_experiment
from .types import Experiment

Strategy = Literal["active", "random", "fixed"]


@dataclass
class DiagnosisStep:
    step: int
    strategy: Strategy
    experiment_name: str
    initial_state: str
    time: float
    observable: str
    shots: int
    score: float | None
    measured_expectation: float
    plus_count: int
    minus_count: int
    map_vector: list[float]
    mean_vector: list[float]
    std_vector: list[float]
    map_confidence: float
    posterior_entropy: float
    effective_sample_size: float
    relative_error: float
    detected_drift_index: int
    correct_drift_location: bool


@dataclass
class DiagnosisResult:
    strategy: Strategy
    stopped_early: bool
    stop_reason: str
    steps: list[DiagnosisStep]
    final_map_vector: list[float]
    final_mean_vector: list[float]
    final_std_vector: list[float]
    final_map_confidence: float

    def to_dict(self) -> dict:
        return asdict(self)


def precompute_predictions(
    posterior: ParticlePosterior,
    experiments: list[Experiment],
) -> PredictionCache:
    cache = PredictionCache()
    for experiment in experiments:
        values = prediction_vector(
            posterior.particles,
            posterior.num_qubits,
            experiment,
            exact_expectation,
        )
        cache.put(experiment, values)
    return cache


def run_diagnosis(
    hidden: TFIMParams,
    nominal: TFIMParams,
    posterior: ParticlePosterior,
    experiments: list[Experiment],
    max_steps: int,
    strategy: Strategy = "active",
    seed: int = 0,
    cache: PredictionCache | None = None,
    *,
    active_score: ActiveScore = "information_gain",
    repeat_penalty: float = 0.35,
    min_steps: int = 1,
    stop_map_confidence: float | None = None,
) -> DiagnosisResult:
    if max_steps <= 0:
        raise ValueError("max_steps must be positive")
    if min_steps <= 0:
        raise ValueError("min_steps must be positive")
    if not experiments:
        raise ValueError("experiment space cannot be empty")
    if cache is None:
        cache = precompute_predictions(posterior, experiments)

    rng = random.Random(seed)
    used_counts: dict[tuple[str, float, str, int], int] = {}
    steps: list[DiagnosisStep] = []
    truth = hidden.as_vector()
    nominal_vector = nominal.as_vector()
    stopped_early = False
    stop_reason = "max_steps"

    for step_index in range(max_steps):
        score: float | None = None
        if strategy == "active":
            experiment, score = choose_active_experiment(
                posterior,
                experiments,
                cache,
                used_counts,
                score_method=active_score,
                repeat_penalty=repeat_penalty,
            )
        elif strategy == "random":
            experiment = choose_random_experiment(experiments, rng)
        elif strategy == "fixed":
            experiment = choose_fixed_experiment(experiments, step_index)
        else:
            raise ValueError(f"unknown strategy: {strategy}")

        used_counts[experiment.key] = used_counts.get(experiment.key, 0) + 1
        measurement_seed = seed * 100_000 + step_index + 1
        result = run_experiment(hidden, experiment, seed=measurement_seed)
        predictions = cache.require(experiment)
        posterior.update_from_predictions(predictions, result)

        map_vector = posterior.map_vector()
        mean_vector = posterior.mean_vector()
        std_vector = posterior.std_vector()
        step = DiagnosisStep(
            step=step_index + 1,
            strategy=strategy,
            experiment_name=experiment.label,
            initial_state=experiment.initial_state,
            time=experiment.time,
            observable=experiment.observable,
            shots=experiment.shots,
            score=score,
            measured_expectation=result.expectation,
            plus_count=result.plus_count,
            minus_count=result.minus_count,
            map_vector=map_vector.tolist(),
            mean_vector=mean_vector.tolist(),
            std_vector=std_vector.tolist(),
            map_confidence=posterior.map_confidence(),
            posterior_entropy=posterior.entropy(),
            effective_sample_size=posterior.effective_sample_size(),
            relative_error=relative_parameter_error(map_vector, truth),
            detected_drift_index=detected_drift_index(map_vector, nominal_vector),
            correct_drift_location=drift_location_correct(map_vector, truth, nominal_vector),
        )
        steps.append(step)

        if (
            stop_map_confidence is not None
            and len(steps) >= min_steps
            and posterior.map_confidence() >= stop_map_confidence
        ):
            stopped_early = True
            stop_reason = f"map_confidence>={stop_map_confidence:g}"
            break

    return DiagnosisResult(
        strategy=strategy,
        stopped_early=stopped_early,
        stop_reason=stop_reason,
        steps=steps,
        final_map_vector=posterior.map_vector().tolist(),
        final_mean_vector=posterior.mean_vector().tolist(),
        final_std_vector=posterior.std_vector().tolist(),
        final_map_confidence=posterior.map_confidence(),
    )
