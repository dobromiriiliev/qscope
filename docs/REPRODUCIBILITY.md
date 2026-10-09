# Reproducibility

The judged path should work from a clean environment without credentials.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
qscope demo --config configs/mvp.json
qscope benchmark --config configs/mvp.json --trials 8
```

The main config stores the hidden Hamiltonian, prior, experiment space, shot count, and random seed. Generated outputs go under `artifacts/` and are excluded from Git by default.

Before submission:

```bash
python -m pip install -e '.[dev]'
pytest -q
ruff check src tests scripts ui
qscope validate-submission --root .
```

For the Qollab page, record the Python/Qiskit versions used for the final benchmark and include the exact config file that produced the headline result.
