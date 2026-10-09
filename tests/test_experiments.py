import pytest

from qscope.experiments import make_experiment_space, summarize_experiment_space
from qscope.types import Experiment


def test_experiment_validation():
    Experiment("++", 0.5, "ZZ", 100).validate(2)


def test_identity_rejected():
    with pytest.raises(ValueError):
        Experiment("00", 0.5, "II", 100).validate(2)


def test_space_cartesian_product():
    exps = make_experiment_space(2, ["00", "++"], [0.2, 0.5], ["ZZ", "XI"], 100)
    assert len(exps) == 8
    summary = summarize_experiment_space(exps)
    assert summary == {"total": 8, "initial_states": 2, "times": 2, "observables": 2}
