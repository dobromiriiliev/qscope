import numpy as np

from qscope.inference import ParticlePosterior
from qscope.policies import information_gain_score, score_experiment


def test_information_gain_zero_when_models_agree():
    posterior = ParticlePosterior.uniform(np.array([[0.0], [1.0]]), 2)
    assert information_gain_score(posterior, np.array([0.3, 0.3])) < 1e-12


def test_information_gain_positive_when_models_disagree():
    posterior = ParticlePosterior.uniform(np.array([[0.0], [1.0]]), 2)
    score = information_gain_score(posterior, np.array([-0.9, 0.9]))
    assert score > 0.4


def test_variance_score():
    posterior = ParticlePosterior.uniform(np.array([[0.0], [1.0]]), 2)
    assert score_experiment(posterior, np.array([-1.0, 1.0]), "variance") == 1.0
