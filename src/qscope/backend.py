from __future__ import annotations

from qscope.model import Observation
from qscope.physics import basis_rotation, parity_sign
from qscope.predictor import ExactPredictor


class LocalQiskitBackend:
    def __init__(self, true_params):
        self._true_params = true_params
        self._predictor = ExactPredictor()

    def run(self, experiment, seed: int) -> Observation:
        state = self._predictor.evolved_state(
            self._true_params,
            experiment.initial_state,
            experiment.evolution_time,
        )
        rotation, qubits = basis_rotation(experiment.observable, self._true_params.n_qubits)
        rotated = state.evolve(rotation)
        rotated.seed(seed)
        counts = rotated.sample_counts(experiment.shots)
        plus = 0
        minus = 0
        for bitstring, count in counts.items():
            if parity_sign(str(bitstring), qubits) > 0:
                plus += int(count)
            else:
                minus += int(count)
        expectation = (plus - minus) / experiment.shots
        return Observation(experiment.id, experiment.shots, plus, minus, float(expectation))
