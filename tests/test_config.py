from pathlib import Path

from qscope.config import build_from_config, load_config

ROOT = Path(__file__).resolve().parents[1]


def test_smoke_config_builds():
    config = load_config(ROOT / "configs" / "smoke.json")
    nominal, hidden, posterior, experiments = build_from_config(config)
    assert nominal.num_qubits == 2
    assert hidden.num_qubits == 2
    assert len(posterior.particles) == 7
    assert len(experiments) == 12
