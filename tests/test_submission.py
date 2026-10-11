from qscope.submission import validate_submission


def test_submission_layout():
    assert validate_submission(".") == []
