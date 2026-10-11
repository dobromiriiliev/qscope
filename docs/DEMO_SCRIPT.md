# Demo notes

A short project demonstration is easiest to follow in this order:

1. Show the four-qubit nominal model and the hidden drift setup.
2. Explain that the posterior begins uniform across 60 candidate Hamiltonians.
3. Show the adaptive experiment sequence and the `LOCALIZE -> CALIBRATE` switch.
4. Show the final fault location, drift estimate, confidence, and credible interval.
5. Show the off-grid benchmark and explain why `+/-0.275` cannot be an exact grid lookup.

Keep the emphasis on the decision loop: Q-Scope uses its current uncertainty to decide which measurement is worth taking next.
