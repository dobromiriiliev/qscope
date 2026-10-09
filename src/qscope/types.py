from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Experiment:
    """One candidate experiment. Strings use q0-first order for readability."""

    initial_state: str
    time: float
    observable: str
    shots: int = 512
    name: str = ""

    def validate(self, num_qubits: int) -> None:
        if len(self.initial_state) != num_qubits:
            raise ValueError("initial_state length must equal num_qubits")
        if len(self.observable) != num_qubits:
            raise ValueError("observable length must equal num_qubits")
        if any(c not in "01+-" for c in self.initial_state):
            raise ValueError("initial_state may only contain 0, 1, +, -")
        if any(c not in "IXYZ" for c in self.observable):
            raise ValueError("observable may only contain I, X, Y, Z")
        if set(self.observable) == {"I"}:
            raise ValueError("observable cannot be identity only")
        if self.time < 0:
            raise ValueError("time must be non-negative")
        if self.shots <= 0:
            raise ValueError("shots must be positive")

    @property
    def key(self) -> tuple[str, float, str, int]:
        return (self.initial_state, float(self.time), self.observable, int(self.shots))

    @property
    def label(self) -> str:
        return self.name or f"{self.initial_state}|t={self.time:g}|{self.observable}"


@dataclass(frozen=True)
class MeasurementResult:
    expectation: float
    plus_count: int
    minus_count: int
    shots: int
    counts: Mapping[str, int]

    def validate(self) -> None:
        if self.plus_count < 0 or self.minus_count < 0:
            raise ValueError("counts cannot be negative")
        if self.plus_count + self.minus_count != self.shots:
            raise ValueError("plus_count + minus_count must equal shots")
        if not -1.0 <= self.expectation <= 1.0:
            raise ValueError("expectation must lie in [-1, 1]")
