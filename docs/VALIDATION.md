# Validation

The validation benchmark is designed to avoid an exact grid lookup.

## Held-out drift values

The inference grid uses `0.05` increments, while the benchmark hides

```text
delta_true in {-0.275, +0.275}.
```

Each value lies exactly halfway between adjacent grid points. The benchmark crosses those two drift values with the three candidate locations `ZZ_01`, `ZZ_12`, and `ZZ_23`.

The single-file Qollab benchmark uses two paired seeds, producing 12 cases per policy.

## Policies

- **Q-Scope:** hierarchical expected information gain.
- **Random:** random selection from the same experiment bank.
- **Fixed:** a predetermined schedule from the same experiment bank.

All policies receive the same shots per round, experiment bank, hypothesis grid, stopping rule, and 15-round budget.

## Success definition

A case is successful only if

```text
stopping target reached
and inferred location == true location
and |delta_hat - delta_true| <= 0.075.
```

The benchmark also reports mean absolute drift error and 90% credible-interval coverage.

## Current seeded Qollab run

The current validated run produced:

```text
Target reached
Q-Scope  100%
Random     0%
Fixed     17%
```

and

```text
Mean absolute drift error
Q-Scope  0.019
Random   0.052
Fixed    0.111
```

These are results from the current seeded configuration, not universal performance claims. Re-run the benchmark after changing the hypothesis grid, experiment bank, shot count, stopping thresholds, or acquisition policy.
