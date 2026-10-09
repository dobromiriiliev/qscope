from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class TFIMParams:
    """Nearest-neighbor ZZ couplings plus local X fields."""

    J_zz: tuple[float, ...]
    h_x: tuple[float, ...]

    @property
    def num_qubits(self) -> int:
        return len(self.h_x)

    def validate(self) -> None:
        if self.num_qubits < 2:
            raise ValueError("TFIM requires at least 2 qubits")
        if len(self.J_zz) != self.num_qubits - 1:
            raise ValueError("J_zz must have num_qubits - 1 entries")
        if not np.all(np.isfinite(self.as_vector(validate=False))):
            raise ValueError("Hamiltonian parameters must be finite")

    def as_vector(self, *, validate: bool = True) -> np.ndarray:
        if validate:
            self.validate()
        return np.asarray((*self.J_zz, *self.h_x), dtype=float)

    def to_dict(self) -> dict[str, list[float]]:
        return {"J_zz": list(self.J_zz), "h_x": list(self.h_x)}

    @classmethod
    def from_vector(cls, vector: Iterable[float], num_qubits: int) -> "TFIMParams":
        v = np.asarray(tuple(vector), dtype=float)
        expected = (num_qubits - 1) + num_qubits
        if v.size != expected:
            raise ValueError(f"expected {expected} parameters, received {v.size}")
        split = num_qubits - 1
        obj = cls(tuple(v[:split]), tuple(v[split:]))
        obj.validate()
        return obj

    @classmethod
    def from_dict(cls, data: dict) -> "TFIMParams":
        obj = cls(tuple(map(float, data["J_zz"])), tuple(map(float, data["h_x"])))
        obj.validate()
        return obj


def parameter_names(num_qubits: int) -> list[str]:
    if num_qubits < 2:
        raise ValueError("num_qubits must be at least 2")
    return [f"J_{i}{i+1}" for i in range(num_qubits - 1)] + [f"h_{i}" for i in range(num_qubits)]


def q0_first_to_qiskit_label(label: str) -> str:
    """Qiskit Pauli labels place the highest-index qubit on the left."""
    return label[::-1]


def single_term_label(num_qubits: int, ops: dict[int, str]) -> str:
    chars = ["I"] * num_qubits
    for qubit, op in ops.items():
        if not 0 <= qubit < num_qubits:
            raise ValueError("qubit index out of range")
        if op not in "XYZ":
            raise ValueError("Pauli operation must be X, Y, or Z")
        chars[qubit] = op
    return q0_first_to_qiskit_label("".join(chars))


def build_tfim_operator(params: TFIMParams):
    """Build a Qiskit SparsePauliOp lazily so pure-Python tests do not require Qiskit."""
    from qiskit.quantum_info import SparsePauliOp

    params.validate()
    n = params.num_qubits
    terms: list[tuple[str, float]] = []
    for i, coupling in enumerate(params.J_zz):
        terms.append((single_term_label(n, {i: "Z", i + 1: "Z"}), float(coupling)))
    for i, field in enumerate(params.h_x):
        terms.append((single_term_label(n, {i: "X"}), float(field)))
    return SparsePauliOp.from_list(terms)
