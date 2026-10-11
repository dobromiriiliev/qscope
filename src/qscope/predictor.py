from __future__ import annotations

import numpy as np

from qscope.experiments import preparation_circuit
from qscope.physics import build_hamiltonian, observable_operator


class ExactPredictor:
    def __init__(self):
        self._states = {}

    def initial_state(self, state_name: str, n_qubits: int):
        from qiskit.quantum_info import Statevector

        return Statevector.from_instruction(preparation_circuit(state_name, n_qubits))

    def evolved_state(self, params, state_name: str, time: float):
        from qiskit.circuit.library import PauliEvolutionGate
        from qiskit.synthesis import MatrixExponential

        key = (params, state_name, float(time))
        state = self._states.get(key)
        if state is None:
            initial = self.initial_state(state_name, params.n_qubits)
            gate = PauliEvolutionGate(
                build_hamiltonian(params),
                time=float(time),
                synthesis=MatrixExponential(),
            )
            state = initial.evolve(gate)
            self._states[key] = state
        return state

    def expectation(self, params, experiment) -> float:
        state = self.evolved_state(params, experiment.initial_state, experiment.evolution_time)
        value = state.expectation_value(observable_operator(experiment.observable, params.n_qubits))
        return float(np.real_if_close(value).real)

    def p_plus(self, params, experiment) -> float:
        value = self.expectation(params, experiment)
        return float(np.clip((1.0 + value) / 2.0, 1e-12, 1.0 - 1e-12))
