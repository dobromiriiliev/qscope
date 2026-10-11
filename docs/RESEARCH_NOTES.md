# Research notes

Q-Scope is motivated by Hamiltonian-learning problems where a useful nominal model is already available but one or more parameters change over time.

The closest conceptual reference for the project is **Meta Hamiltonian Learning** by Bienias, Seif, and Hafezi (2021). That work studies repeated Hamiltonian characterization when a nominal model is known but parameters can drift. Q-Scope does not reproduce the published method. It uses a small discrete hypothesis model, exact small-system Qiskit simulation, finite-shot Bayesian inference, and a hierarchical active measurement policy.

The current prototype deliberately narrows the problem to one drifting nearest-neighbor `ZZ` coupling in a four-qubit transverse-field Ising model. This keeps the experiment selection transparent enough to inspect and benchmark end to end.

Useful follow-up directions include local `X`-field drift, simultaneous drift terms, continuous parameter inference, explicit decoherence/readout models, hardware execution, and online tracking of time-dependent drift.
