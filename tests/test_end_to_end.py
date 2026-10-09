import pytest

pytest.importorskip("qiskit")

from qscope.config import build_from_config, load_config
from qscope.diagnosis import run_diagnosis


def test_two_step_diagnosis_runs():
    config = load_config("configs/smoke.json")
    nominal, hidden, posterior, experiments = build_from_config(config)
    result = run_diagnosis(hidden, nominal, posterior, experiments, max_steps=2, seed=4)
    assert len(result.steps) == 2
    assert len(result.final_map_vector) == 3
