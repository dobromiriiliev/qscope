# Algorithm

Q-Scope models diagnosis as sequential Bayesian experimental design.

## Hamiltonian

The nominal four-qubit transverse-field Ising Hamiltonian is

```text
H0 = sum_(i=0)^2 J_i Z_i Z_(i+1) + sum_(i=0)^3 h_i X_i.
```

The default parameters are `J_i = 1.0` and `h_i = 0.5`. A candidate fault is

```text
H(r, delta) = H0 + delta P_r,
```

where `P_r` is one of `Z0Z1`, `Z1Z2`, or `Z2Z3`.

The discrete hypothesis set is

```text
H = {(r, delta) : r in {01,12,23}, delta in Delta}
```

with

```text
Delta = {-0.50, -0.45, ..., -0.05, +0.05, ..., +0.50}.
```

There are `3 x 20 = 60` hypotheses.

## Experiment model

An experiment is

```text
e = (|psi0>, t, M),
```

where `|psi0>` is `|0000>` or `|++++>`, `t` is one of seven evolution times, and `M` is one of seven Pauli observables. There are 98 experiments.

For hypothesis `h`, the evolved state is

```text
|psi_h(t)> = exp(-i H_h t) |psi0>.
```

The expectation of `M` is

```text
mu(h,e) = <psi_h(t)| M |psi_h(t)>.
```

Since the measured Pauli observables have eigenvalues `+1` and `-1`,

```text
p_plus(h,e) = (1 + mu(h,e)) / 2.
```

Qiskit computes these predictions once and they are cached as a `60 x 98` matrix.

## Finite-shot likelihood

Each selected experiment uses `N = 128` shots. If `K` is the number of `+1` outcomes,

```text
K | h,e ~ Binomial(N, p_plus(h,e)).
```

The likelihood is

```text
P(K=k | h,e) = C(N,k) p^k (1-p)^(N-k).
```

## Bayesian update

Let `D_t` be the data collected through round `t`. After experiment `e_t` returns `k`,

```text
P(h | D_t) proportional to P(k | h,e_t) P(h | D_(t-1)).
```

The implementation performs the update in log space and normalizes with `logsumexp`.

## Localization

The location marginal is

```text
P(R=r | D) = sum_delta P(r,delta | D).
```

Location entropy is

```text
H(R | D) = -sum_r P(r | D) log P(r | D).
```

For candidate experiment `e`, the exact finite-shot expected information gain is

```text
EIG_R(e)
  = H(R | D)
    - sum_(k=0)^N P(k | e,D) H(R | D,k,e).
```

Q-Scope selects

```text
e* = argmax_e EIG_R(e).
```

## Calibration

When

```text
max_r P(R=r | D) >= 0.90,
```

let `r*` be the leading location. Q-Scope conditions on that location:

```text
P(delta | r*,D) = P(r*,delta | D) / P(r* | D).
```

It then scores candidate experiments by expected information gain about `delta`:

```text
EIG_Delta(e)
  = H(Delta | r*,D)
    - sum_k P(k | e,r*,D) H(Delta | r*,D,k,e).
```

Again,

```text
e* = argmax_e EIG_Delta(e).
```

## Estimate and stopping

The posterior mean drift is

```text
delta_hat = sum_delta delta P(delta | r*,D).
```

The reported 90% credible interval is taken directly from the discrete posterior. A run stops successfully when

```text
P(r* | D) >= 0.98
```

and

```text
width(CI_90) <= 0.05.
```

The hard budget is 15 rounds, or 1920 shots at 128 shots per round.

## Implementation notes

The reusable package also contains an optional posterior-predictive mismatch warning. It is not part of the headline Qollab result because out-of-family errors can sometimes be approximated by an allowed drift hypothesis; the warning should not be treated as a proof of model correctness.
