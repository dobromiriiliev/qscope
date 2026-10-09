# Q-Scope

**Active Hamiltonian learning for quantum-system diagnostics.**

Q-Scope is a hackathon project that asks: if a quantum system drifts, can we learn **what to measure next** instead of following a fixed measurement schedule?

The MVP uses a small transverse-field Ising model, hides a drift in one nearest-neighbor coupling, generates finite-shot measurements with Qiskit, updates a posterior over candidate Hamiltonians, and chooses the next experiment by expected information gain. The active strategy is benchmarked against random and fixed probing.

## Why this repo is structured this way

The judging path must work on a free local simulator, so the default project has **no cloud dependency, API key, or hardware requirement**. Qiskit is the only quantum framework used by the core implementation. The repository is MIT licensed and includes the pieces needed for a Qollab submission: runnable notebook, project-page draft, demo script, originality disclosure, tests, CI, and reproducibility instructions.

## Physics

The MVP Hamiltonian is

```text
H = sum_i J_i Z_i Z_(i+1) + sum_i h_i X_i
```

For four qubits, Q-Scope assumes the nominal Hamiltonian is known approximately and one selected coupling may have drifted. This intentionally narrow prior makes the inference loop easy to explain and benchmark during the hackathon.

## Core loop

```text
Hidden Hamiltonian
      |
      v
Choose experiment  <-------------------+
      |                                |
      v                                |
Run Qiskit simulation                  |
      |                                |
      v                                |
Finite-shot Pauli measurement          |
      |                                |
      v                                |
Bayesian posterior update              |
      |                                |
      +----> score next experiments ---+
```

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .

qscope inspect --config configs/mvp.json
qscope demo --config configs/mvp.json
qscope benchmark --config configs/mvp.json --trials 8
```

Outputs are written to `artifacts/`.

Run tests and submission checks:

```bash
python -m pip install -e '.[dev]'
pytest -q
ruff check src tests scripts ui
qscope validate-submission --root .
```

Optional Streamlit UI:

```bash
python -m pip install -e '.[ui]'
streamlit run ui/app.py
```

## Repository layout

```text
qscope-complete/
├── .github/workflows/ci.yml
├── configs/
│   ├── mvp.json
│   └── smoke.json
├── docs/
│   ├── ALGORITHM.md
│   ├── ARCHITECTURE.md
│   ├── DEMO_SCRIPT.md
│   ├── HACKATHON_CHECKLIST.md
│   ├── QOLLAB_PROJECT_PAGE.md
│   ├── REPRODUCIBILITY.md
│   └── RESEARCH_NOTES.md
├── notebooks/qollab_demo.ipynb
├── scripts/
├── src/qscope/
├── tests/
├── ui/app.py
├── LICENSE
├── ORIGINALITY.md
├── TEAM.md
└── pyproject.toml
```

## Commands

### Inspect the configured experiment

```bash
qscope inspect --config configs/mvp.json
```

### Run active diagnosis

```bash
qscope demo --config configs/mvp.json
```

Override the policy for comparison:

```bash
qscope demo --config configs/mvp.json --strategy random
qscope demo --config configs/mvp.json --strategy fixed
```

### Benchmark policies

```bash
qscope benchmark --config configs/mvp.json --trials 8
```

This creates:

- `artifacts/benchmark_raw.csv`
- `artifacts/benchmark_summary.csv`
- `artifacts/benchmark_headline.json`
- `artifacts/benchmark.png`

### Validate submission structure

```bash
qscope validate-submission --root .
```

## Active learning

Each candidate experiment is defined by

```python
Experiment(
    initial_state="++++",
    time=0.75,
    observable="IIZZ",
    shots=512,
)
```

For every remaining candidate Hamiltonian, Q-Scope predicts the expectation value for that experiment. The default policy estimates the one-shot expected information gain and chooses the experiment with the highest score, with a mild repeat penalty. A simpler posterior-weighted variance score is also supported.

## MVP benchmark

The primary comparison is:

```text
active selection vs random selection vs fixed schedule
```

All strategies get the same shot budget and experiment budget. The headline metrics are relative parameter error and the number of experiments required to reach a target reconstruction error. Do not claim a numerical advantage until you have run the benchmark and saved the resulting artifact.

## Extending the project

The clean extension points are:

1. Add new Hamiltonian parameter classes and builders.
2. Add new experiment families or initial states.
3. Add a richer prior for multiple simultaneous drifts.
4. Add new active-learning scores.
5. Add a backend adapter after the local path is stable.

Do **not** make hardware access a requirement for the judged path.

## Hackathon submission files

- `docs/QOLLAB_PROJECT_PAGE.md` — project-page draft
- `docs/DEMO_SCRIPT.md` — 2–3 minute video outline
- `ORIGINALITY.md` — prior-work/template disclosure
- `TEAM.md` — role split
- `LICENSE` — MIT

## License

MIT. See `LICENSE`.
