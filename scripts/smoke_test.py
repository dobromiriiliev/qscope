#!/usr/bin/env python3
"""Fast end-to-end check for a fresh clone."""

from qscope.config import build_from_config, load_config
from qscope.diagnosis import run_diagnosis


def main() -> None:
    config = load_config("configs/smoke.json")
    nominal, hidden, posterior, experiments = build_from_config(config)
    result = run_diagnosis(
        hidden,
        nominal,
        posterior,
        experiments,
        max_steps=2,
        seed=11,
        strategy="active",
    )
    assert len(result.steps) == 2
    print("Q-Scope smoke test passed")


if __name__ == "__main__":
    main()
