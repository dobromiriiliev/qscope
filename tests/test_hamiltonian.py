import numpy as np
import pytest

from qscope.hamiltonian import TFIMParams, parameter_names, q0_first_to_qiskit_label


def test_roundtrip_vector():
    params = TFIMParams((1.0, 0.9, 0.8), (0.5, 0.5, 0.5, 0.5))
    restored = TFIMParams.from_vector(params.as_vector(), 4)
    assert restored == params


def test_parameter_names():
    assert parameter_names(3) == ["J_01", "J_12", "h_0", "h_1", "h_2"]


def test_qiskit_label_reversal():
    assert q0_first_to_qiskit_label("ZZII") == "IIZZ"


def test_invalid_shape():
    with pytest.raises(ValueError):
        TFIMParams((1.0, 1.0), (0.5, 0.5)).validate()
