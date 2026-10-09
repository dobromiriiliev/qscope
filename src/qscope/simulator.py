from __future__ import annotations

import math

from .hamiltonian import TFIMParams, build_tfim_operator, q0_first_to_qiskit_label
from .types import Experiment, MeasurementResult


def _qiskit_imports():
    try:
        from qiskit import QuantumCircuit
        from qiskit.circuit.library import PauliEvolutionGate
        from qiskit.quantum_info import Pauli, Statevector
        from qiskit.synthesis import MatrixExponential
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Qiskit is required for simulation. Install the project with `pip install -e .`."
        ) from exc
    return QuantumCircuit, PauliEvolutionGate, Pauli, Statevector, MatrixExponential


def _prepare_product_state(circuit, state: str) -> None:
    for q, symbol in enumerate(state):
        if symbol == "0":
            continue
        if symbol == "1":
            circuit.x(q)
        elif symbol == "+":
            circuit.h(q)
        elif symbol == "-":
            circuit.x(q)
            circuit.h(q)
        else:
            raise ValueError(f"unsupported initial-state symbol: {symbol}")


def build_evolution_circuit(params: TFIMParams, experiment: Experiment):
    QuantumCircuit, PauliEvolutionGate, _, _, MatrixExponential = _qiskit_imports()
    params.validate()
    experiment.validate(params.num_qubits)
    circuit = QuantumCircuit(params.num_qubits)
    _prepare_product_state(circuit, experiment.initial_state)
    evolution = PauliEvolutionGate(
        build_tfim_operator(params),
        time=experiment.time,
        synthesis=MatrixExponential(),
    )
    circuit.append(evolution, range(params.num_qubits))
    return circuit


def exact_expectation(params: TFIMParams, experiment: Experiment) -> float:
    """Exact Pauli expectation used by candidate-model inference."""
    _, _, Pauli, Statevector, _ = _qiskit_imports()
    circuit = build_evolution_circuit(params, experiment)
    state = Statevector.from_instruction(circuit)
    observable = Pauli(q0_first_to_qiskit_label(experiment.observable))
    value = state.expectation_value(observable)
    return float(value.real)


def _add_measurement_basis_rotation(circuit, observable: str) -> None:
    for q, op in enumerate(observable):
        if op == "X":
            circuit.h(q)
        elif op == "Y":
            circuit.sdg(q)
            circuit.h(q)
        elif op in "ZI":
            continue
        else:
            raise ValueError(f"unsupported observable symbol: {op}")


def _observable_eigenvalue(bitstring: str, observable: str) -> int:
    eigenvalue = 1
    for q, op in enumerate(observable):
        if op == "I":
            continue
        bit = bitstring[-1 - q]
        if bit == "1":
            eigenvalue *= -1
    return eigenvalue


def run_experiment(
    params: TFIMParams,
    experiment: Experiment,
    seed: int | None = None,
) -> MeasurementResult:
    """Run one finite-shot local experiment using Qiskit's Statevector sampler."""
    _, _, _, Statevector, _ = _qiskit_imports()
    circuit = build_evolution_circuit(params, experiment)
    _add_measurement_basis_rotation(circuit, experiment.observable)
    state = Statevector.from_instruction(circuit)
    if seed is not None:
        state.seed(seed)
    counts = {str(k): int(v) for k, v in dict(state.sample_counts(experiment.shots)).items()}

    plus = 0
    minus = 0
    for bitstring, count in counts.items():
        if _observable_eigenvalue(bitstring, experiment.observable) == 1:
            plus += count
        else:
            minus += count

    expectation = (plus - minus) / experiment.shots
    if not math.isclose(plus + minus, experiment.shots):
        raise RuntimeError("shot accounting mismatch")

    result = MeasurementResult(
        expectation=float(expectation),
        plus_count=plus,
        minus_count=minus,
        shots=experiment.shots,
        counts=counts,
    )
    result.validate()
    return result
