import pytest

pytest.importorskip("qiskit")

from qscope.config import build_from_config, load_config
from qscope.simulator import exact_expectation, run_experiment


def test_local_qiskit_experiment_runs():
    config = load_config("configs/smoke.json")
    _, hidden, _, experiments = build_from_config(config)
    exp = experiments[0]
    exact = exact_expectation(hidden, exp)
    measured = run_experiment(hidden, exp, seed=123)
    assert -1.0 <= exact <= 1.0
    assert -1.0 <= measured.expectation <= 1.0
    assert measured.plus_count + measured.minus_count == exp.shots
