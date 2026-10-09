# Q-Scope

## One-line summary

Q-Scope is an active Hamiltonian-learning system that chooses which quantum experiment to run next in order to identify hidden drift with fewer measurements.

## Problem

A programmed quantum model can differ from the effective model being executed because interactions or calibration parameters drift. Exhaustively probing every observable is expensive and often wastes measurements.

## What we built

Q-Scope starts from an approximate transverse-field Ising model. We hide a change in one coupling and give Q-Scope only finite-shot measurement results. After every experiment, it updates a posterior over candidate Hamiltonians and chooses the next experiment expected to reduce uncertainty the most.

## Quantum component

The project uses Qiskit to prepare product states, evolve them under a Pauli Hamiltonian, and simulate finite-shot Pauli measurements. The default path runs entirely on a free local simulator and does not require hardware credentials.

## Active learning

For each candidate experiment, Q-Scope predicts what each remaining Hamiltonian would produce. It scores experiments by expected information gain and runs the most informative one next.

## Baselines

We compare against:

1. random experiment selection,
2. a fixed experiment schedule.

All methods receive the same shot and experiment budgets.

## Results

**Replace this section with final benchmark numbers generated from `artifacts/benchmark_headline.json`. Do not invent percentages.**

Include:

- reconstruction error vs experiment number,
- drift-location accuracy,
- number of experiments required to reach the chosen target error.

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
qscope demo --config configs/mvp.json
qscope benchmark --config configs/mvp.json --trials 8
```

## Reproduce the judged result

State the final commit hash, Python version, Qiskit version, config file, and exact benchmark command here before submission.

## Research inspiration

Q-Scope is inspired by work from the Hafezi research group on Hamiltonian learning and extracting hidden quantum structure from measurements. Add the exact references used by the team.

## Limitations

This hackathon version assumes a known Hamiltonian family and a narrow single-drift prior. It uses ideal state evolution plus finite-shot sampling, not a full hardware noise model.

## Originality

See `ORIGINALITY.md` for the exact disclosure of starting material and work completed during the hackathon window.

## License

MIT.
