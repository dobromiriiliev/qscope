# Architecture

The package is intentionally split so the physics, quantum execution, inference, policy, and presentation layers can change independently.

```text
config.json
   |
   +--> TFIMParams -------------------------+
   |                                       |
   +--> experiment space                   |
   |                                       v
   +--> particle prior --> PredictionCache --> active policy
                           ^                  |
                           |                  v
                     exact predictor     chosen experiment
                                              |
                                              v
                                     finite-shot simulator
                                              |
                                              v
                                      posterior update
                                              |
                                              +---- loop
```

## Module responsibilities

- `hamiltonian.py`: parameter representation and Qiskit operator construction
- `experiments.py`: candidate experiment generation
- `simulator.py`: local Qiskit evolution and finite-shot measurements
- `inference.py`: particle prior and Bayesian updates
- `policies.py`: active/random/fixed experiment selection
- `diagnosis.py`: closed-loop orchestration
- `benchmark.py`: fair repeated comparisons
- `metrics.py`: error and drift-location metrics
- `plotting.py`: reproducible figures
- `submission.py`: structural submission checks
- `cli.py`: command-line entry point

## Backend choice

The default implementation uses `Statevector` locally. That keeps the judged path deterministic in structure, free to run, and independent of credentials. If a hardware adapter is added later, keep the same `Experiment -> MeasurementResult` contract so the inference code does not change.
