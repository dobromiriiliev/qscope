import numpy as np

from qscope.config import load_config
from qscope.inference import Belief, bayesian_update, entropy, weighted_quantile
from qscope.model import Hypothesis, TFIMParams
from qscope.physics import apply_drift, build_hypotheses, params_from_config


def test_config_loads():
    cfg = load_config("configs/mvp.json")
    assert cfg.model.n_qubits == 4
    assert cfg.experiments.shots == 128
    assert cfg.hypotheses.include_no_drift is False
    assert cfg.experiments.times[-1] == 1.5


def test_apply_drift_changes_expected_coupling():
    params = TFIMParams(
        4,
        (1.0, 1.0, 1.0),
        (0.5, 0.5, 0.5, 0.5),
    )
    changed = apply_drift(params, "ZZ_23", -0.35)
    assert changed.J == (1.0, 1.0, 0.65)
    assert params.J == (1.0, 1.0, 1.0)


def test_hypothesis_grid_has_no_zero_duplicates():
    cfg = load_config("configs/mvp.json")
    nominal = params_from_config(cfg.model)
    hypotheses = build_hypotheses(nominal, cfg.hypotheses)
    assert len(hypotheses) == 60
    assert all(abs(h.delta) > 1e-12 for h in hypotheses)


def test_location_uniform_prior_equalizes_location_mass():
    params = TFIMParams(2, (1.0,), (0.5, 0.5))
    hypotheses = (
        Hypothesis(0, "none", "NO_DRIFT", 0.0, params),
        Hypothesis(1, "a1", "A", -0.2, params),
        Hypothesis(2, "a2", "A", 0.2, params),
        Hypothesis(3, "b1", "B", -0.2, params),
        Hypothesis(4, "b2", "B", 0.2, params),
    )
    belief = Belief.location_uniform(hypotheses)
    posterior = belief.location_posterior()
    assert np.isclose(posterior["NO_DRIFT"], 1 / 3)
    assert np.isclose(posterior["A"], 1 / 3)
    assert np.isclose(posterior["B"], 1 / 3)


def test_entropy_handles_zero_probabilities():
    value = entropy(np.array([0.0, 0.25, 0.75]))
    expected = -(0.25 * np.log(0.25) + 0.75 * np.log(0.75))
    assert np.isfinite(value)
    assert np.isclose(value, expected)


def test_weighted_quantile_returns_grid_value():
    values = np.array([-0.2, 0.0, 0.2])
    weights = np.array([0.1, 0.8, 0.1])
    assert weighted_quantile(values, weights, 0.05) == -0.2
    assert weighted_quantile(values, weights, 0.5) == 0.0
    assert weighted_quantile(values, weights, 0.95) == 0.2


def test_bayesian_update_normalizes_and_moves_weight():
    params = TFIMParams(2, (1.0,), (0.5, 0.5))
    hypotheses = (
        Hypothesis(0, "a", "A", -0.1, params),
        Hypothesis(1, "b", "B", 0.1, params),
    )
    belief = Belief.uniform(hypotheses)
    updated = bayesian_update(belief, np.log(np.array([0.1, 0.9])))
    assert np.isclose(updated.weights.sum(), 1.0)
    assert updated.weights[1] > updated.weights[0]
