# Q-Scope

Q-Scope is an adaptive Hamiltonian-drift diagnostic built with Qiskit. It starts from a calibrated four-qubit transverse-field Ising model, assumes that one nearest-neighbor `ZZ` coupling may have drifted, and chooses each new measurement from the posterior produced by the measurements collected so far.

The core idea is simple:

```text
predict -> choose -> measure -> update -> repeat
```

Q-Scope first **localizes** the drifting coupling and then **calibrates** its magnitude. The final benchmark compares this adaptive strategy with random and fixed probing under the same experiment bank, shot count, stopping rule, and round budget.

This effort is supported by Qollab & IonQ.

## Model

The nominal Hamiltonian is

```text
H0 = sum_i J_i Z_i Z_(i+1) + sum_i h_i X_i
```

with

```text
J01 = J12 = J23 = 1.00
h0 = h1 = h2 = h3 = 0.50
```

A candidate drift model is

```text
H(r, delta) = H0 + delta P_r
```

where `r` is one of `ZZ_01`, `ZZ_12`, or `ZZ_23`. The default demonstration hides a drift at `ZZ_23` with `delta = -0.35`, so the true `J23` value is `0.65`.

The hypothesis grid contains 20 nonzero drift values per location from `-0.50` through `+0.50` in increments of `0.05`, giving 60 candidate Hamiltonians.

## Adaptive policy

Each experiment is a tuple

```text
e = (initial state, evolution time, observable)
```

from two initial states, seven evolution times, and seven observables. That produces 98 candidate experiments.

For each hypothesis and experiment, Qiskit predicts

```text
p(+1 | h, e) = (1 + <M>_(h,e)) / 2.
```

Each selected experiment is sampled with 128 shots. The observed `+1` count is modeled with a binomial likelihood and used to update the posterior in log space.

During `LOCALIZE`, Q-Scope maximizes expected information gain over the three fault locations. When the leading location reaches 90% posterior probability, the policy switches to `CALIBRATE` and maximizes expected information gain over drift magnitude at that location.

The default run stops when the location posterior reaches 98% and the 90% credible interval for drift is no wider than `0.05`, or after 15 rounds.

See [`docs/ALGORITHM.md`](docs/ALGORITHM.md) for the full derivation.

## Repository layout

```text
main.py                 single-file Qollab entry point
src/qscope/              reusable package implementation
configs/                 MVP and smoke configurations
scripts/                 local run and validation helpers
tests/                   unit and integration tests
docs/                    algorithm, validation, and Qollab documentation
visuals/                 source for the project thumbnail
assets/                  reference outputs from the validated demo
```

## Quick start

Use Python 3.11-3.13.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

Run the tests:

```bash
pytest -q
```

Inspect the full configuration:

```bash
qscope inspect --config configs/mvp.json
```

Run the package demo:

```bash
qscope demo --config configs/mvp.json
```

Run the package benchmark:

```bash
qscope benchmark --config configs/mvp.json --trials 2
```

Run the Qollab single-file version locally:

```bash
python -c "import main; main.main()"
```

That writes:

```text
qscope_dashboard.png
qscope_protocol.png
qscope_measurement.png
qscope_offgrid_benchmark.png
qscope_results.json
```

## Off-grid validation

The inference grid is spaced by `0.05`, but the benchmark hides `delta = -0.275` and `+0.275`, exactly halfway between adjacent grid values. The six physical cases are the three possible drift locations crossed with the two off-grid drift values. Two paired seeds are used by the single-file Qollab benchmark, giving 12 cases per policy.

A case is counted as successful only when the stopping target is reached, the correct coupling is identified, and

```text
|delta_hat - delta_true| <= 0.075.
```

The current validated Qollab run produced a 100% target-reached rate for Q-Scope, compared with 17% for Fixed and 0% for Random. Mean absolute drift error was `0.019` for Q-Scope, `0.052` for Random, and `0.111` for Fixed. These numbers are included as a record of that seeded run; regenerate the benchmark before making new claims after changing the model or policy.

More detail is in [`docs/VALIDATION.md`](docs/VALIDATION.md).

## Qollab

The submitted Qollab path is intentionally self-contained. `main.py` contains the complete four-qubit demo, adaptive inference loop, plotting code, and off-grid benchmark. It requires only:

```text
qiskit
numpy
scipy
matplotlib
```

No cloud credentials or remote hardware account are needed.

The text used for the Qollab project page is in [`docs/QOLLAB_PROJECT_PAGE.md`](docs/QOLLAB_PROJECT_PAGE.md).

## Research context

Q-Scope is motivated by repeated Hamiltonian-characterization problems where a nominal Hamiltonian is already useful but one or more parameters drift over time. The closest conceptual reference for the project is the Hafezi Group's Meta Hamiltonian Learning setting. Q-Scope is not a reproduction of that method; it uses a transparent discrete Bayesian hypothesis model and hierarchical active experiment selection.

See [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md).

## Scope

The current prototype deliberately focuses on one drifting nearest-neighbor `ZZ` coupling in a four-qubit model. It does not claim arbitrary Hamiltonian reconstruction, large-system scalability, quantum advantage, simultaneous multi-fault recovery, or real-hardware validation.

## License

MIT. See [`LICENSE`](LICENSE).
