import numpy as np

from qscope.cache import LikelihoodCache, PredictionCache
from qscope.inference import Belief
from qscope.model import Experiment, Hypothesis, TFIMParams
from qscope.policies import HierarchicalInformationPolicy


def test_policy_prefers_discriminating_experiment():
    params = TFIMParams(2, (1.0,), (0.5, 0.5))
    hypotheses = (
        Hypothesis(0, "a", "A", -0.2, params),
        Hypothesis(1, "b", "B", 0.2, params),
    )
    experiments = (
        Experiment(0, "00", 0.2, "ZZ_01", 20),
        Experiment(1, "00", 0.4, "ZZ_01", 20),
    )
    predictions = PredictionCache(np.array([[0.50, 0.05], [0.50, 0.95]], dtype=float))
    likelihoods = LikelihoodCache.build(predictions, experiments)
    belief = Belief.uniform(hypotheses)
    decision = HierarchicalInformationPolicy(0.8).select(belief, experiments, predictions, likelihoods)
    assert decision.experiment_id == 1
    assert decision.mode == "LOCALIZE"


def test_policy_switches_to_calibration():
    params = TFIMParams(2, (1.0,), (0.5, 0.5))
    hypotheses = (
        Hypothesis(0, "a1", "A", -0.2, params),
        Hypothesis(1, "a2", "A", 0.2, params),
        Hypothesis(2, "b1", "B", -0.2, params),
    )
    experiments = (Experiment(0, "00", 0.2, "ZZ_01", 20),)
    predictions = PredictionCache(np.array([[0.1], [0.9], [0.5]], dtype=float))
    likelihoods = LikelihoodCache.build(predictions, experiments)
    belief = Belief(hypotheses, np.array([0.45, 0.45, 0.10]))
    decision = HierarchicalInformationPolicy(0.8).select(belief, experiments, predictions, likelihoods)
    assert decision.mode == "CALIBRATE"
