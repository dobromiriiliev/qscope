from __future__ import annotations

from qscope.backend import LocalQiskitBackend
from qscope.cache import LikelihoodCache, PredictionCache
from qscope.diagnosis import DiagnosisEngine, MismatchDetector, StoppingRule
from qscope.experiments import build_experiments
from qscope.inference import Belief
from qscope.physics import apply_drift, build_hypotheses, params_from_config
from qscope.policies import HierarchicalInformationPolicy
from qscope.predictor import ExactPredictor


def build_components(cfg):
    nominal = params_from_config(cfg.model)
    hypotheses = build_hypotheses(nominal, cfg.hypotheses)
    experiments = build_experiments(cfg.experiments)
    predictions = PredictionCache.build(hypotheses, experiments, ExactPredictor())
    likelihoods = LikelihoodCache.build(predictions, experiments)
    return nominal, hypotheses, experiments, predictions, likelihoods


def build_engine(cfg, nominal, hypotheses, experiments, predictions, likelihoods, policy=None, seed=None):
    true_params = apply_drift(nominal, cfg.hidden_system.drift_term, cfg.hidden_system.delta)
    return DiagnosisEngine(
        hypotheses=hypotheses,
        experiments=experiments,
        predictions=predictions,
        likelihoods=likelihoods,
        backend=LocalQiskitBackend(true_params),
        policy=policy or HierarchicalInformationPolicy(cfg.policy.switch_confidence),
        belief=Belief.location_uniform(hypotheses),
        stopping_rule=StoppingRule(cfg.stopping),
        mismatch_detector=MismatchDetector(cfg.mismatch.predictive_p_value, cfg.mismatch.consecutive_failures),
        seed=cfg.seed if seed is None else seed,
    )
