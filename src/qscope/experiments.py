from __future__ import annotations

from itertools import product

from .types import Experiment


def make_experiment_space(
    num_qubits: int,
    initial_states: list[str],
    times: list[float],
    observables: list[str],
    shots: int,
) -> list[Experiment]:
    experiments: list[Experiment] = []
    seen: set[tuple[str, float, str, int]] = set()
    for state, time, observable in product(initial_states, times, observables):
        exp = Experiment(
            initial_state=state,
            time=float(time),
            observable=observable,
            shots=int(shots),
            name=f"{state}|t={float(time):g}|{observable}",
        )
        exp.validate(num_qubits)
        if exp.key not in seen:
            experiments.append(exp)
            seen.add(exp.key)
    if not experiments:
        raise ValueError("experiment space is empty")
    return experiments


def summarize_experiment_space(experiments: list[Experiment]) -> dict[str, int]:
    return {
        "total": len(experiments),
        "initial_states": len({e.initial_state for e in experiments}),
        "times": len({e.time for e in experiments}),
        "observables": len({e.observable for e in experiments}),
    }
