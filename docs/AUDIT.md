# Repository audit

The repository contains two execution paths:

- `main.py`: the self-contained Qollab demonstration and benchmark.
- `src/qscope/`: a reusable package implementation with CLI commands and tests.

The default MVP uses 4 qubits, 60 nonzero drift hypotheses, 98 experiments, 128 shots per selected experiment, a 90% localization-to-calibration switch, a 98% final location threshold, a 0.05 maximum 90% credible-interval width, and a 15-round budget.

The benchmark uses hidden drift values `-0.275` and `+0.275`, which do not occur on the 0.05-spaced inference grid.

Generated caches and local virtual environments are excluded from version control. The project is MIT licensed and does not include credentials or remote-service requirements in the judged path.
