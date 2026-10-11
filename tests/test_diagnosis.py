import numpy as np

from qscope.diagnosis import MismatchDetector, StoppingRule
from qscope.inference import Belief
from qscope.model import Hypothesis, TFIMParams


class StopConfig:
    location_confidence = 0.95
    credible_interval_width = 0.1
    max_experiments = 10


def test_no_drift_can_stop():
    params = TFIMParams(2, (1.0,), (0.5, 0.5))
    hypotheses = (
        Hypothesis(0, "none", "NO_DRIFT", 0.0, params),
        Hypothesis(1, "drift", "A", 0.2, params),
    )
    belief = Belief(hypotheses, np.array([0.97, 0.03]))
    assert StoppingRule(StopConfig()).check(belief, 2, False) == "SUCCESS"


def test_mismatch_counts_consecutive_failures():
    detector = MismatchDetector(0.05, 2)
    detector.failures = 1
    assert not detector.triggered
    detector.failures = 2
    assert detector.triggered
