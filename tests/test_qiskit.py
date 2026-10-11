import pytest

pytest.importorskip("qiskit")

from qscope.backend import LocalQiskitBackend
from qscope.config import load_config
from qscope.factory import build_components, build_engine
from qscope.model import Experiment, TFIMParams
from qscope.predictor import ExactPredictor


def test_exact_predictor_known_zz_eigenstate():
    params = TFIMParams(2, (1.0,), (0.0, 0.0))
    experiment = Experiment(0, "00", 0.7, "ZZ_01", 100)
    probability = ExactPredictor().p_plus(params, experiment)
    assert probability > 1.0 - 1e-9


def test_local_backend_is_reproducible_for_same_seed():
    params = TFIMParams(2, (1.0,), (0.5, 0.5))
    experiment = Experiment(0, "++", 0.4, "X_0", 100)
    backend = LocalQiskitBackend(params)
    first = backend.run(experiment, 1234)
    second = backend.run(experiment, 1234)
    assert first.plus_count == second.plus_count
    assert first.minus_count == second.minus_count


def test_smoke_qiskit_run():
    cfg = load_config("configs/smoke.json")
    nominal, hypotheses, experiments, predictions, likelihoods = build_components(cfg)
    result = build_engine(
        cfg,
        nominal,
        hypotheses,
        experiments,
        predictions,
        likelihoods,
    ).run()
    assert result.experiments_used <= cfg.stopping.max_experiments
    assert result.status in {"SUCCESS", "MAX_BUDGET", "MODEL_MISMATCH"}
