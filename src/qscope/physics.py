from __future__ import annotations

from dataclasses import replace

import numpy as np

from qscope.model import Hypothesis, TFIMParams


def params_from_config(cfg) -> TFIMParams:
    return TFIMParams(cfg.n_qubits, cfg.J, cfg.h)


def build_hamiltonian(params: TFIMParams):
    from qiskit.quantum_info import SparsePauliOp

    terms = [("ZZ", [i, i + 1], coeff) for i, coeff in enumerate(params.J)]
    terms.extend(("X", [i], coeff) for i, coeff in enumerate(params.h))
    return SparsePauliOp.from_sparse_list(terms, num_qubits=params.n_qubits).simplify()


def apply_drift(params: TFIMParams, term: str | None, delta: float) -> TFIMParams:
    if term is None or term == "NO_DRIFT" or abs(delta) < 1e-15:
        return params
    if term.startswith("ZZ_"):
        suffix = term.split("_", 1)[1]
        if len(suffix) != 2 or not suffix.isdigit():
            raise ValueError(f"invalid drift term: {term}")
        i, j = int(suffix[0]), int(suffix[1])
        if j != i + 1 or i < 0 or j >= params.n_qubits:
            raise ValueError(f"invalid nearest-neighbor term: {term}")
        values = list(params.J)
        values[i] += delta
        return replace(params, J=tuple(values))
    if term.startswith("X_"):
        i = int(term.split("_", 1)[1])
        if i < 0 or i >= params.n_qubits:
            raise ValueError(f"invalid field term: {term}")
        values = list(params.h)
        values[i] += delta
        return replace(params, h=tuple(values))
    raise ValueError(f"unsupported drift term: {term}")


def _grid(start: float, stop: float, step: float) -> list[float]:
    count = int(round((stop - start) / step))
    return [float(np.round(start + i * step, 12)) for i in range(count + 1)]


def build_hypotheses(nominal: TFIMParams, cfg) -> list[Hypothesis]:
    hypotheses: list[Hypothesis] = []
    if cfg.include_no_drift:
        hypotheses.append(Hypothesis(0, "NO_DRIFT", "NO_DRIFT", 0.0, nominal))
    values = [x for x in _grid(cfg.delta_min, cfg.delta_max, cfg.delta_step) if abs(x) > 1e-12]
    for term in cfg.terms:
        for delta in values:
            idx = len(hypotheses)
            hypotheses.append(
                Hypothesis(idx, f"{term}:{delta:+.6g}", term, delta, apply_drift(nominal, term, delta))
            )
    return hypotheses


def parse_observable(name: str) -> tuple[str, tuple[int, ...]]:
    if "_" not in name:
        raise ValueError(f"invalid observable: {name}")
    pauli, suffix = name.split("_", 1)
    if len(pauli) == 1 and suffix.isdigit():
        return pauli, (int(suffix),)
    if len(pauli) == 2 and len(suffix) == 2 and suffix.isdigit():
        return pauli, (int(suffix[0]), int(suffix[1]))
    raise ValueError(f"invalid observable: {name}")


def observable_operator(name: str, n_qubits: int):
    from qiskit.quantum_info import SparsePauliOp

    pauli, qubits = parse_observable(name)
    if any(q < 0 or q >= n_qubits for q in qubits):
        raise ValueError(f"observable outside system: {name}")
    return SparsePauliOp.from_sparse_list([(pauli, list(qubits), 1.0)], num_qubits=n_qubits)


def basis_rotation(name: str, n_qubits: int):
    from qiskit import QuantumCircuit

    pauli, qubits = parse_observable(name)
    circuit = QuantumCircuit(n_qubits)
    for symbol, qubit in zip(pauli, qubits):
        if symbol == "X":
            circuit.h(qubit)
        elif symbol == "Y":
            circuit.sdg(qubit)
            circuit.h(qubit)
        elif symbol != "Z":
            raise ValueError(f"unsupported Pauli symbol: {symbol}")
    return circuit, qubits


def parity_sign(bitstring: str, qubits: tuple[int, ...]) -> int:
    bits = bitstring.replace(" ", "")[::-1]
    parity = sum(int(bits[q]) for q in qubits) % 2
    return 1 if parity == 0 else -1
