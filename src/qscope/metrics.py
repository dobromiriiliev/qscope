from __future__ import annotations

import numpy as np


def relative_parameter_error(estimate: np.ndarray, truth: np.ndarray) -> float:
    estimate = np.asarray(estimate, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimate.shape != truth.shape:
        raise ValueError("estimate and truth must have the same shape")
    denom = float(np.linalg.norm(truth))
    if denom == 0:
        return float(np.linalg.norm(estimate - truth))
    return float(np.linalg.norm(estimate - truth) / denom)


def parameter_rmse(estimate: np.ndarray, truth: np.ndarray) -> float:
    estimate = np.asarray(estimate, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimate.shape != truth.shape:
        raise ValueError("estimate and truth must have the same shape")
    return float(np.sqrt(np.mean(np.square(estimate - truth))))


def detected_drift_index(estimate: np.ndarray, nominal: np.ndarray) -> int:
    estimate = np.asarray(estimate, dtype=float)
    nominal = np.asarray(nominal, dtype=float)
    if estimate.shape != nominal.shape:
        raise ValueError("estimate and nominal must have the same shape")
    return int(np.argmax(np.abs(estimate - nominal)))


def true_drift_index(truth: np.ndarray, nominal: np.ndarray) -> int:
    return detected_drift_index(truth, nominal)


def drift_location_correct(estimate: np.ndarray, truth: np.ndarray, nominal: np.ndarray) -> bool:
    return detected_drift_index(estimate, nominal) == true_drift_index(truth, nominal)
