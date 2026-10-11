# Q-Scope

## Adaptive Hamiltonian Drift Diagnosis with Qiskit

**Q-Scope turns quantum characterization into an active decision process.**  
It identifies which Hamiltonian interaction drifted, estimates the new value, and chooses each measurement based on what the previous measurements revealed.

**4 qubits · 60 candidate Hamiltonians · 98 possible experiments · 128 shots per round**

---

## What Q-Scope does

A calibrated quantum system can drift away from its intended Hamiltonian.  
The usual response is to rerun a fixed characterization sequence.

Q-Scope takes a different approach:

```text
Q-SCOPE

Nominal Hamiltonian H₀
        |
        v
60 candidate drift models H(r, δ)
        |
        v
98 candidate experiments e = (|ψ₀>, t, M)
        |
        v
Adaptive measurement policy
LOCALIZE  ->  CALIBRATE
        |
        v
Finite-shot observation K ~ Binomial(N, p)
        |
        v
Bayesian posterior P(r, δ | D)
        |
        v
Final diagnosis
r* + δ̂ + confidence interval
```

At every round, Q-Scope asks one question:

**Which available experiment is expected to remove the most uncertainty right now?**

---

## Results snapshot

The current off-grid validation run shows a clear gap between adaptive and non-adaptive probing.

### Successful diagnoses
Higher is better.

```text
Q-Scope   ████████████████████████████████████████  100%
Fixed     ███████                                  17%
Random                                             0%
```

### Mean absolute drift error
Lower is better.

```text
Q-Scope   ███████                                  0.019
Random    ███████████████████                      0.052
Fixed     ████████████████████████████████████████ 0.111
```

These results come from the same off-grid cases and equal measurement budgets.

---

# Physical model

The current prototype uses a four-qubit transverse-field Ising model.

```text
   h₀=0.50          h₁=0.50          h₂=0.50          h₃=0.50
      |                |                |                |
      X                X                X                X
      |                |                |                |
   [ q0 ] --J₀₁=1.00-- [ q1 ] --J₁₂=1.00-- [ q2 ] --J₂₃=1.00-- [ q3 ]
```

The nominal Hamiltonian is

```text
H₀ = Σᵢ Jᵢ Zᵢ Zᵢ₊₁ + Σᵢ hᵢ Xᵢ

for i = 0,1,2 in the ZZ term
and i = 0,1,2,3 in the X term.
```

For the default system:

```text
J₀₁ = J₁₂ = J₂₃ = 1.00

h₀ = h₁ = h₂ = h₃ = 0.50
```

One nearest-neighbor `ZZ` coupling is allowed to drift.

The hidden system is modeled as

```text
H_true = H₀ + δ Pᵣ
```

where:

- `r ∈ {01, 12, 23}` identifies the drifting coupling,
- `Pᵣ ∈ {Z₀Z₁, Z₁Z₂, Z₂Z₃}`,
- `δ` is the unknown drift magnitude.

The default demonstration hides:

```text
r_true = 23
δ_true = -0.35

J₂₃,true = 1.00 + (-0.35) = 0.65
```

The diagnostic algorithm is never given `r_true` or `δ_true`.  
It only sees finite-shot measurement outcomes.

---

# Hypothesis model

Q-Scope begins with three possible fault locations:

```text
R ∈ {J₀₁, J₁₂, J₂₃}
```

For each location, it considers 20 nonzero drift magnitudes:

```text
Δ = {-0.50, -0.45, ..., -0.10, -0.05,
      +0.05, +0.10, ..., +0.45, +0.50}
```

A single hypothesis is:

```text
h = (r, δ)
```

with candidate Hamiltonian

```text
H(r, δ) = H₀ + δ Pᵣ
```

The full hypothesis set is therefore:

```text
|R| x |Δ| = 3 x 20 = 60 hypotheses
```

Examples:

- `(J₀₁, -0.40)`
- `(J₁₂, +0.15)`
- `(J₂₃, -0.35)`

The initial prior is uniform:

```text
P(r, δ) = 1 / 60
```

for every candidate pair `(r, δ)`.

---

# Experiment space

Every candidate experiment is represented as

```text
e = (|ψ₀>, t, M)
```

where:

- `|ψ₀>` is the prepared initial state,
- `t` is the evolution time,
- `M` is the measured Pauli observable.

## Initial states

```text
|0000>
|++++>
```

with

```text
|+> = (|0> + |1>) / √2
```

so

```text
|++++> = |+> ⊗ |+> ⊗ |+> ⊗ |+>
```

## Evolution times

```text
t ∈ {0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5}
```

## Observables

```text
M ∈ {Z₀Z₁, Z₁Z₂, Z₂Z₃, X₀, X₁, X₂, X₃}
```

The complete experiment bank contains

```text
2 states x 7 times x 7 observables = 98 experiments
```

All benchmark policies use this exact same experiment bank.

---

# Qiskit forward model

Qiskit is used to predict the measurement statistics under every candidate Hamiltonian.

For hypothesis `h = (r, δ)` and experiment `e = (|ψ₀>, t, M)`, the state evolves as

```text
|ψ_h(t)> = exp(-i H(r, δ) t) |ψ₀>
```

The expected value of observable `M` is

```text
μ(h, e) = <ψ_h(t)| M |ψ_h(t)>
```

Because each measured Pauli observable has eigenvalues `+1` and `-1`,

```text
p₊(h, e) = P(+1 | h, e)
          = (1 + μ(h, e)) / 2
```

and

```text
p₋(h, e) = 1 - p₊(h, e)
```

The implementation uses:

- `SparsePauliOp` for `H` and `M`,
- `PauliEvolutionGate` for `exp(-iHt)`,
- `Statevector` for the exact four-qubit state,
- finite-shot sampling for observed measurements.

Before diagnosis begins, Q-Scope builds the prediction matrix

```text
P[h, e] = p₊(h, e)
```

with shape

```text
60 hypotheses x 98 experiments.
```

Conceptually:

```text
                e₁       e₂       e₃      ...      e₉₈

h₁             0.51     0.74     0.16             0.32
h₂             0.49     0.69     0.20             0.39
h₃             0.53     0.25     0.81             0.75
...
h₆₀
```

Caching this matrix means that adaptive experiment selection does not need to rerun the same counterfactual quantum simulation at every round.

---

# Finite-shot observation model

Q-Scope does not observe the exact expectation `μ`.

Each selected experiment is run for

```text
N = 128 shots.
```

For a candidate model predicting `p₊(h,e)`, the number of positive outcomes obeys

```text
K | h,e ~ Binomial(N, p₊(h,e))
```

so

```text
P(K = k | h,e)
    = C(N,k) p₊(h,e)^k [1 - p₊(h,e)]^(N-k)
```

where

```text
C(N,k) = N! / [k!(N-k)!].
```

An observed result might be

```text
K = 76 positive shots

+1 : 76
-1 : 52
```

with empirical expectation

```text
μ̂ = (N₊ - N₋) / N
   = (76 - 52) / 128
   = 0.1875
```

The diagnostic algorithm reasons from the shot count, not from the hidden exact probability.

---

# Bayesian inference

Let `D_t` denote all measurements collected through round `t`.

The posterior over Hamiltonian hypotheses is

```text
P(h | D_t)
```

where `h = (r, δ)`.

After selecting experiment `e_t` and observing `K_t = k`, Bayes' rule gives

```text
P(h | D_t)
    ∝ P(k | h, e_t) P(h | D_{t-1})
```

or explicitly,

```text
P(r, δ | D_t)
    =
      P(k | r, δ, e_t) P(r, δ | D_{t-1})
      ------------------------------------------------
      Σ_{r',δ'} P(k | r',δ',e_t) P(r',δ' | D_{t-1})
```

The implementation evaluates this in log space:

```text
log w'_h = log w_h + log P(k | h,e)
```

followed by

```text
w'_h = exp(log w'_h - logsumexp(log w'))
```

This prevents numerical underflow when repeated measurements drive some hypotheses toward extremely small posterior mass.

---

# Stage 1: fault localization

During localization, the 60-hypothesis posterior is marginalized over drift magnitude.

For a candidate location `r`:

```text
P(R = r | D)
    = Σ_δ P(r, δ | D)
```

Therefore:

```text
P(J₀₁ | D) = Σ_δ P(J₀₁, δ | D)
P(J₁₂ | D) = Σ_δ P(J₁₂, δ | D)
P(J₂₃ | D) = Σ_δ P(J₂₃, δ | D)
```

Initially:

```text
P(J₀₁) = P(J₁₂) = P(J₂₃) = 1/3.
```

The uncertainty in the fault location is quantified with Shannon entropy:

```text
H(R | D)
    = - Σ_r P(r | D) ln P(r | D)
```

A low entropy means one location dominates the posterior.  
A high entropy means several locations remain plausible.

---

# Expected information gain during localization

For each candidate experiment `e`, Q-Scope considers the possible shot counts

```text
k ∈ {0,1,...,128}.
```

The posterior predictive probability of observing count `k` is

```text
P(k | e,D)
    = Σ_h P(k | h,e) P(h | D)
```

If count `k` were observed, the hypothetical updated location entropy would be

```text
H(R | D,k,e).
```

The expected information gain for localization is

```text
EIG_R(e)
    = H(R | D)
      - Σ_k P(k | e,D) H(R | D,k,e)
```

Q-Scope chooses

```text
e* = argmax_e EIG_R(e).
```

In words:

**select the experiment expected to remove the most uncertainty about which coupling drifted.**

---

# Stage 2: magnitude calibration

Once

```text
max_r P(r | D) >= 0.90,
```

Q-Scope defines

```text
r* = argmax_r P(r | D)
```

and switches its acquisition objective.

The conditional drift posterior is

```text
P(δ | r*,D)
    = P(r*,δ | D) / P(r* | D).
```

Its entropy is

```text
H(Δ | r*,D)
    = - Σ_δ P(δ | r*,D) ln P(δ | r*,D).
```

For candidate experiment `e`, the calibration information gain is

```text
EIG_Δ(e)
    = H(Δ | r*,D)
      - Σ_k P(k | e,r*,D) H(Δ | r*,D,k,e).
```

The selected calibration experiment is

```text
e* = argmax_e EIG_Δ(e).
```

This is the mathematical meaning of the two-stage policy:

```text
LOCALIZE
maximize information about R

        ->

CALIBRATE
maximize information about Δ | R = r*
```

---

# Posterior point estimate

For the leading fault location `r*`, Q-Scope reports the posterior mean drift

```text
δ̂
 = E[Δ | r*,D]
 = Σ_δ δ P(δ | r*,D).
```

The inferred coupling value is therefore

```text
Ĵ_r* = J_r*,nominal + δ̂.
```

For the default demonstration, a correct result should be close to

```text
δ_true = -0.35

J₂₃,true = 1.00 - 0.35 = 0.65.
```

---

# Credible interval

Q-Scope also reports a discrete 90% credible interval for `δ`.

If the lower and upper posterior quantiles are `δ_L` and `δ_U`, the interval is

```text
CI₉₀ = [δ_L, δ_U]
```

such that approximately 90% of the conditional posterior mass lies within the interval.

The calibration stopping rule requires

```text
δ_U - δ_L <= 0.05.
```

---

# Stopping rule

A diagnosis is complete when

```text
max_r P(r | D) >= 0.98
```

and

```text
width(CI₉₀) <= 0.05.
```

Equivalently:

```text
location confidence >= 98%
AND
90% drift credible interval <= 0.05 wide.
```

The hard limit is

```text
T_max = 15 adaptive rounds.
```

With `N = 128` shots per round, the maximum shot budget is

```text
N_max = 15 x 128 = 1920 shots.
```

If Q-Scope stops earlier, it uses fewer than 1920 shots.

---

# The adaptive inference loop

```text
POSTERIOR -> SELECT -> MEASURE -> UPDATE -> REPEAT

P(r,δ | D_t)
      |
      v
compute EIG(e) for all 98 experiments
      |
      v
e* = argmax EIG(e)
      |
      v
K_t ~ Binomial(128, p₊(h_true,e*))
      |
      v
P(r,δ | D_{t+1})
      |
      +--> stopping rule satisfied? ---- yes ----> report r*, δ̂, CI₉₀
      |
      no
      |
      v
repeat
```

---

# Why the benchmark is off-grid

The inference grid uses increments of

```text
Δ_grid = 0.05.
```

The benchmark hides

```text
δ_true ∈ {-0.275, +0.275}.
```

These values lie halfway between adjacent grid points:

```text
negative side

-0.30 -------- -0.275 -------- -0.25
 grid            hidden          grid
```

```text
positive side

+0.25 -------- +0.275 -------- +0.30
 grid            hidden          grid
```

Therefore:

```text
δ_true ∉ Δ.
```

The hidden benchmark system does not exactly match any single hypothesis.

Q-Scope must infer an off-grid value through the posterior distribution.

---

# Benchmark scenarios

The benchmark crosses:

```text
3 fault locations
x
2 off-grid drift values
x
2 paired seeds
=
12 cases per policy.
```

The six physical systems are:

- `J₀₁ @ -0.275`
- `J₀₁ @ +0.275`
- `J₁₂ @ -0.275`
- `J₁₂ @ +0.275`
- `J₂₃ @ -0.275`
- `J₂₃ @ +0.275`

Each is evaluated with two finite-shot seeds.

---

# Benchmark policies

## Q-Scope

Uses

```text
e*_t = argmax_e EIG(e | D_t)
```

with the hierarchical localization/calibration objective.

## Random

Samples

```text
e_t ~ Uniform({1,...,98}).
```

## Fixed

Uses a predetermined sequence

```text
e₁, e₂, ..., e₁₅
```

from the same candidate bank.

All policies receive identical:

- experiment spaces,
- shot counts,
- hidden systems,
- stopping criteria,
- maximum round budgets.

---

# Benchmark success criterion

A benchmark trial is considered successful when all three conditions hold:

```text
1. the policy reaches its stopping target

2. r̂ = r_true

3. |δ̂ - δ_true| <= 0.075
```

The parameter error for one trial is

```text
E_δ = |δ̂ - δ_true|.
```

Across `m` benchmark cases, mean absolute drift error is

```text
MAE_δ
    = (1/m) Σ_j |δ̂_j - δ_true,j|.
```

The success rate is

```text
Success Rate
    = (# successful trials / # total trials) x 100%.
```

Credible-interval coverage is

```text
Coverage₉₀
    = (1/m) Σ_j 1[δ_true,j ∈ CI₉₀,j].
```

---

# Current off-grid validation

### Successful diagnoses

```text
Q-Scope   ████████████████████████████████████████  100%
Fixed     ███████                                  17%
Random                                             0%
```

### Mean absolute drift error

```text
Q-Scope   ███████                                  0.019
Random    ███████████████████                      0.052
Fixed     ████████████████████████████████████████ 0.111
```

The same hidden cases and measurement budgets are used for every policy.

---

# Software architecture

```text
+--------------------+       +----------------------+
| Qiskit forward     | ----> | Prediction matrix    |
| model              |       | P[h,e], 60 x 98      |
+--------------------+       +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | Bayesian belief      |
                              | P(r,δ | D)            |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | Acquisition policy   |
                              | EIG_R or EIG_Δ        |
                              +----------+-----------+
                                         |
                                      e*
                                         |
                                         v
+--------------------+       +----------------------+
| hidden H_true      | ----> | finite-shot sampler  |
| r_true, δ_true     |       | K ~ Binomial(128,p)  |
+--------------------+       +----------+-----------+
                                         |
                                         v
                                    observed K
                                         |
                                         +----> Bayes update
```

The true parameters remain inside the hidden simulator.

The acquisition policy receives only:

- `P[h,e]`,
- the current posterior `P(r,δ | D)`,
- measurement history.

There is no direct access to `(r_true, δ_true)`.

---

# Project outputs

A complete run writes five artifacts.

## `qscope_dashboard.png`
Overall diagnosis, localization history, magnitude posterior, and benchmark.

## `qscope_protocol.png`
The exact adaptive measurement sequence and the LOCALIZE-to-CALIBRATE switch.

## `qscope_measurement.png`
Finite-shot evidence from the final selected experiment.

## `qscope_offgrid_benchmark.png`
Q-Scope vs Random vs Fixed on the off-grid cases.

## `qscope_results.json`
Machine-readable diagnosis, posterior statistics, adaptive history, and benchmark summary.

The numerical values in these outputs come from the actual run.

---

# Running Q-Scope

Q-Scope runs directly as a Python/Qiskit project.

Required packages:

- `qiskit`
- `numpy`
- `scipy`
- `matplotlib`

No external API key or cloud account is required for the submitted path.

Run `main.py`.

A successful run reports:

```text
Q-Scope
Adaptive diagnosis of a drifting transverse-field Ising model

Model           4 qubits, 3 candidate ZZ couplings
Hypotheses      60
Measurements    98 candidate experiments
Shots / round   128
```

followed by the diagnosis and off-grid benchmark.

---

# Reproducibility

The important experimental constants are explicit:

```text
N                         = 128 shots
T_max                     = 15 rounds
localization switch       = 0.90
final location threshold  = 0.98
max CI₉₀ width            = 0.05

r_true,default            = J₂₃
δ_true,default            = -0.35

δ_off-grid                = {-0.275, +0.275}
```

Finite-shot sampling uses explicit seeds.

The benchmark uses paired seeds so competing policies are evaluated under comparable stochastic conditions.

---

# Research context

Q-Scope is motivated by Hamiltonian-learning settings in which a quantum system already has a useful nominal model but must be characterized again as its parameters drift.

A closely related setting appears in repeated Hamiltonian characterization, including the Hafezi Group's work on Meta Hamiltonian Learning.

The shared problem is:

```text
known approximate H₀
        +
unknown parameter drift δ
        =
re-characterization
```

Q-Scope explores this problem with:

```text
structured H(r,δ) hypotheses
+
Qiskit forward simulation
+
finite-shot likelihoods
+
Bayesian inference
+
active experimental design
```

It is not a direct implementation of Meta Hamiltonian Learning. The research motivates the problem; Q-Scope uses a different inference and acquisition strategy designed to remain inspectable end to end.

---

# Scope

The current prototype intentionally focuses on a controlled problem:

- four qubits,
- known transverse-field Ising structure,
- one drifting nearest-neighbor `ZZ` coupling,
- discrete drift hypotheses,
- finite experiment bank,
- simulator-generated measurements.

It does not claim:

- arbitrary Hamiltonian reconstruction,
- large-system scalability,
- quantum advantage,
- multiple simultaneous fault recovery,
- real-hardware validation.

These constraints make it possible to test the adaptive measurement policy cleanly and reproducibly.

---

# Where it goes next

The same architecture naturally extends to:

```text
H₀ + one unknown ZZ drift
          |
          v
H₀ + unknown local X drift
          |
          v
multiple δₖ terms
          |
          v
continuous posterior p(θ | D)
          |
          v
noise-aware likelihood p(y | θ,e)
          |
          v
hardware backend
          |
          v
online tracking θ(t)
```

A useful next ablation is to compare the hierarchical policy against a single acquisition objective used through the entire diagnosis.

---

## In one sentence

**Q-Scope learns what changed in a quantum system by learning what to measure next.**

---

This effort is supported by **Qollab & IonQ**  
License: **MIT**
