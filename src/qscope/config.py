from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelConfig:
    type: str
    n_qubits: int
    J: tuple[float, ...]
    h: tuple[float, ...]


@dataclass(frozen=True)
class HiddenSystemConfig:
    drift_term: str | None
    delta: float


@dataclass(frozen=True)
class HypothesisConfig:
    terms: tuple[str, ...]
    delta_min: float
    delta_max: float
    delta_step: float
    include_no_drift: bool


@dataclass(frozen=True)
class ExperimentConfig:
    states: tuple[str, ...]
    times: tuple[float, ...]
    observables: tuple[str, ...]
    shots: int


@dataclass(frozen=True)
class PolicyConfig:
    switch_confidence: float


@dataclass(frozen=True)
class StoppingConfig:
    location_confidence: float
    credible_interval_width: float
    max_experiments: int


@dataclass(frozen=True)
class MismatchConfig:
    predictive_p_value: float
    consecutive_failures: int


@dataclass(frozen=True)
class AppConfig:
    model: ModelConfig
    hidden_system: HiddenSystemConfig
    hypotheses: HypothesisConfig
    experiments: ExperimentConfig
    policy: PolicyConfig
    stopping: StoppingConfig
    mismatch: MismatchConfig
    seed: int


def _validate(cfg: AppConfig) -> None:
    if cfg.model.type != "tfim":
        raise ValueError("model.type must be tfim")
    if cfg.model.n_qubits < 2:
        raise ValueError("n_qubits must be at least 2")
    if len(cfg.model.J) != cfg.model.n_qubits - 1:
        raise ValueError("J must have n_qubits - 1 values")
    if len(cfg.model.h) != cfg.model.n_qubits:
        raise ValueError("h must have n_qubits values")
    if cfg.hypotheses.delta_step <= 0:
        raise ValueError("delta_step must be positive")
    if cfg.hypotheses.delta_min >= cfg.hypotheses.delta_max:
        raise ValueError("delta_min must be less than delta_max")
    if cfg.experiments.shots <= 0:
        raise ValueError("shots must be positive")
    if not cfg.experiments.states or not cfg.experiments.times or not cfg.experiments.observables:
        raise ValueError("experiment space cannot be empty")
    if not 0 < cfg.policy.switch_confidence < 1:
        raise ValueError("switch_confidence must be in (0, 1)")
    if not 0 < cfg.stopping.location_confidence < 1:
        raise ValueError("location_confidence must be in (0, 1)")
    if cfg.stopping.credible_interval_width <= 0:
        raise ValueError("credible_interval_width must be positive")
    if cfg.stopping.max_experiments <= 0:
        raise ValueError("max_experiments must be positive")
    if not 0 < cfg.mismatch.predictive_p_value < 1:
        raise ValueError("predictive_p_value must be in (0, 1)")
    if cfg.mismatch.consecutive_failures <= 0:
        raise ValueError("consecutive_failures must be positive")


def load_config(path: str | Path) -> AppConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg = AppConfig(
        model=ModelConfig(
            type=str(data["model"].get("type", "tfim")),
            n_qubits=int(data["model"]["n_qubits"]),
            J=tuple(float(x) for x in data["model"]["J"]),
            h=tuple(float(x) for x in data["model"]["h"]),
        ),
        hidden_system=HiddenSystemConfig(
            drift_term=data["hidden_system"].get("drift_term"),
            delta=float(data["hidden_system"]["delta"]),
        ),
        hypotheses=HypothesisConfig(
            terms=tuple(str(x) for x in data["hypotheses"]["terms"]),
            delta_min=float(data["hypotheses"]["delta_min"]),
            delta_max=float(data["hypotheses"]["delta_max"]),
            delta_step=float(data["hypotheses"]["delta_step"]),
            include_no_drift=bool(data["hypotheses"].get("include_no_drift", True)),
        ),
        experiments=ExperimentConfig(
            states=tuple(str(x) for x in data["experiments"]["states"]),
            times=tuple(float(x) for x in data["experiments"]["times"]),
            observables=tuple(str(x) for x in data["experiments"]["observables"]),
            shots=int(data["experiments"]["shots"]),
        ),
        policy=PolicyConfig(float(data["policy"]["switch_confidence"])),
        stopping=StoppingConfig(
            location_confidence=float(data["stopping"]["location_confidence"]),
            credible_interval_width=float(data["stopping"]["credible_interval_width"]),
            max_experiments=int(data["stopping"]["max_experiments"]),
        ),
        mismatch=MismatchConfig(
            predictive_p_value=float(data["mismatch"]["predictive_p_value"]),
            consecutive_failures=int(data["mismatch"]["consecutive_failures"]),
        ),
        seed=int(data.get("seed", 42)),
    )
    _validate(cfg)
    return cfg
