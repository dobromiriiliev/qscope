from __future__ import annotations

import json
from pathlib import Path

from .experiments import make_experiment_space
from .hamiltonian import TFIMParams
from .inference import ParticlePosterior, make_single_drift_particles


def load_config(path: str | Path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    validate_config(config)
    return config


def validate_config(config: dict) -> None:
    required = {
        "schema_version",
        "num_qubits",
        "nominal",
        "hidden",
        "prior",
        "experiment_space",
        "diagnosis",
        "benchmark",
    }
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"config is missing required keys: {missing}")
    if int(config["schema_version"]) != 1:
        raise ValueError("unsupported config schema_version")

    n = int(config["num_qubits"])
    if n < 2 or n > 8:
        raise ValueError("num_qubits should be between 2 and 8 for this hackathon scaffold")

    nominal = TFIMParams.from_dict(config["nominal"])
    hidden = TFIMParams.from_dict(config["hidden"])
    if nominal.num_qubits != n or hidden.num_qubits != n:
        raise ValueError("config num_qubits does not match parameter lengths")

    prior = config["prior"]
    if prior.get("mode") != "single_parameter_grid":
        raise ValueError("only prior.mode='single_parameter_grid' is supported in the MVP")

    exp_cfg = config["experiment_space"]
    make_experiment_space(
        n,
        list(exp_cfg["initial_states"]),
        list(map(float, exp_cfg["times"])),
        list(exp_cfg["observables"]),
        int(exp_cfg["shots"]),
    )

    diagnosis = config["diagnosis"]
    if int(diagnosis["max_steps"]) <= 0:
        raise ValueError("diagnosis.max_steps must be positive")
    if diagnosis.get("active_score", "information_gain") not in {"variance", "information_gain"}:
        raise ValueError("diagnosis.active_score must be variance or information_gain")


def build_from_config(config: dict):
    validate_config(config)
    n = int(config["num_qubits"])
    nominal = TFIMParams.from_dict(config["nominal"])
    hidden = TFIMParams.from_dict(config["hidden"])

    prior = config["prior"]
    particles = make_single_drift_particles(
        nominal=nominal,
        parameter_indices=list(map(int, prior["drift_parameter_indices"])),
        low=float(prior["drift_low"]),
        high=float(prior["drift_high"]),
        values_per_parameter=int(prior["values_per_parameter"]),
    )
    posterior = ParticlePosterior.uniform(particles, n)

    exp_cfg = config["experiment_space"]
    experiments = make_experiment_space(
        num_qubits=n,
        initial_states=list(exp_cfg["initial_states"]),
        times=list(map(float, exp_cfg["times"])),
        observables=list(exp_cfg["observables"]),
        shots=int(exp_cfg["shots"]),
    )
    return nominal, hidden, posterior, experiments
