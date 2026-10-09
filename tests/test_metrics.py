import numpy as np

from qscope.metrics import detected_drift_index, drift_location_correct, relative_parameter_error


def test_detected_drift_index():
    nominal = np.array([1.0, 1.0, 0.5])
    estimate = np.array([1.0, 0.6, 0.5])
    assert detected_drift_index(estimate, nominal) == 1


def test_drift_location_correct():
    nominal = np.array([1.0, 1.0])
    truth = np.array([0.6, 1.0])
    estimate = np.array([0.7, 0.95])
    assert drift_location_correct(estimate, truth, nominal)


def test_relative_error_zero():
    x = np.array([1.0, 2.0])
    assert relative_parameter_error(x, x) == 0.0
