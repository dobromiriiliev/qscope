from __future__ import annotations

from itertools import product

from qscope.model import Experiment


def preparation_circuit(name: str, n_qubits: int):
    from qiskit import QuantumCircuit

    if len(name) != n_qubits:
        raise ValueError(f"state {name} does not match {n_qubits} qubits")
    circuit = QuantumCircuit(n_qubits)
    for qubit, symbol in enumerate(reversed(name)):
        if symbol == "0":
            continue
        if symbol == "1":
            circuit.x(qubit)
        elif symbol == "+":
            circuit.h(qubit)
        elif symbol == "-":
            circuit.x(qubit)
            circuit.h(qubit)
        else:
            raise ValueError(f"unsupported state symbol: {symbol}")
    return circuit


def build_experiments(cfg) -> list[Experiment]:
    return [
        Experiment(idx, state, float(time), observable, cfg.shots)
        for idx, (state, time, observable) in enumerate(product(cfg.states, cfg.times, cfg.observables))
    ]
