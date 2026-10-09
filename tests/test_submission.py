from pathlib import Path

from qscope.submission import checks_passed, validate_repository

ROOT = Path(__file__).resolve().parents[1]


def test_repository_submission_structure():
    checks = validate_repository(ROOT)
    assert checks_passed(checks), [c for c in checks if not c.passed]
