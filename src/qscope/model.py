from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TFIMParams:
    n_qubits: int
    J: tuple[float, ...]
    h: tuple[float, ...]


@dataclass(frozen=True)
class Hypothesis:
    id: int
    label: str
    location: str
    delta: float
    params: TFIMParams


@dataclass(frozen=True)
class Experiment:
    id: int
    initial_state: str
    evolution_time: float
    observable: str
    shots: int


@dataclass(frozen=True)
class Observation:
    experiment_id: int
    shots: int
    plus_count: int
    minus_count: int
    expectation: float
