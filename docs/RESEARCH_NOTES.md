# Research notes

Use this file as the team's scientific notebook. Keep claims conservative and separate research inspiration from what the hackathon implementation actually demonstrates.

## Hafezi-group connection

The project is motivated by Hamiltonian learning and the broader idea that hidden properties of a quantum system can be inferred efficiently from carefully chosen measurements. Add the exact papers/pages the team reads here, with short notes on what was borrowed conceptually.

## MVP assumptions

- The functional form of the TFIM Hamiltonian is known.
- Only one selected `ZZ` coupling drifts at a time.
- Candidate parameters lie on a finite grid.
- State preparation and measurement basis changes are ideal.
- The local statevector simulator provides the system dynamics.
- Finite-shot sampling is included, but hardware noise is not.

## Claims we can support

If the benchmark shows it, we can claim that adaptive experiment selection reaches a target reconstruction error in fewer experiments than the chosen random/fixed baselines for the tested simulator scenarios.

## Claims we should not make without evidence

- quantum advantage
- superiority on real hardware
- scalable device tomography
- robustness to realistic hardware noise
- general reconstruction of arbitrary Hamiltonians

## Primary references

- Hafezi Group, "Machine Learning in Quantum Systems": https://hafezi.jqi.umd.edu/research/machine-learning-quantum-systems
- Bienias, Seif, and Hafezi, "Meta Hamiltonian Learning" (2021): https://hafezi.jqi.umd.edu/publications/meta-hamiltonian-learning
- Hafezi Group, "Quantum Simulation": https://hafezi.jqi.umd.edu/research/quantum-simulation

The quantum-simulation page explicitly frames verification of the implemented Hamiltonian and efficient characterization/measurement of quantum systems as central research questions. The hackathon project uses that as motivation, but the implementation here is a small simulator-based proof of concept rather than a reproduction of the group's research code.
