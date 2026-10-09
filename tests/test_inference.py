import numpy as np

from qscope.hamiltonian import TFIMParams
from qscope.inference import ParticlePosterior, make_single_drift_particles
from qscope.types import MeasurementResult


def test_particle_prior_deduplicates_nominal_crossing():
    nominal = TFIMParams((1.0, 1.0), (0.5, 0.5, 0.5))
    particles = make_single_drift_particles(nominal, [0, 1], 0.5, 1.5, 3)
    assert len(particles) == 5


def test_bayesian_update_favors_positive_prediction():
    particles = np.array([[0.0], [1.0]])
    posterior = ParticlePosterior.uniform(particles, num_qubits=2)
    result = MeasurementResult(expectation=1.0, plus_count=20, minus_count=0, shots=20, counts={"00": 20})
    posterior.update_from_predictions(np.array([-0.8, 0.8]), result)
    assert posterior.weights[1] > 0.999


def test_posterior_statistics():
    particles = np.array([[0.0, 1.0], [2.0, 3.0]])
    posterior = ParticlePosterior.uniform(particles, num_qubits=2)
    assert np.allclose(posterior.mean_vector(), [1.0, 2.0])
    assert np.allclose(posterior.std_vector(), [1.0, 1.0])
    assert posterior.effective_sample_size() == 2.0
