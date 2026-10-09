# Algorithm

## 1. Candidate Hamiltonians

The MVP starts from a nominal TFIM and assumes exactly one selected coupling may have drifted. A grid of candidate parameter vectors forms a discrete prior.

## 2. Candidate experiments

An experiment contains:

- a product initial state,
- evolution time,
- Pauli observable,
- shot count.

## 3. Forward model

For each candidate Hamiltonian and experiment, Q-Scope computes the exact expectation value

```text
mu(theta, e) = <psi(theta,e)| O_e |psi(theta,e)>
```

This prediction table is cached because the same candidate experiments are scored repeatedly.

## 4. Measurement likelihood

A Pauli measurement has outcomes +1 and -1. If the predicted expectation is `mu`, then

```text
p(+1 | theta,e) = (1 + mu) / 2
p(-1 | theta,e) = (1 - mu) / 2
```

Finite-shot counts therefore have a binomial likelihood. The posterior weights are updated in log space.

## 5. Active selection

The default score is expected one-shot information gain. For each possible outcome, Q-Scope computes the hypothetical posterior and its entropy. The chosen experiment maximizes

```text
H(prior) - E_y[H(posterior | y,e)]
```

A small repeat penalty prevents one experiment from dominating simply because it remains marginally informative.

## 6. Baselines

- `random`: uniformly sample from the same experiment set
- `fixed`: cycle through the same experiment set in a deterministic order

All strategies receive the same shot count per experiment and the same maximum number of experiments.
