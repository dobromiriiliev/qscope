# Contributing

Keep changes small enough to review quickly during the hackathon.

1. Branch from `main`.
2. Run `ruff check src tests scripts ui`.
3. Run `pytest -q`.
4. If you change physics assumptions, update `docs/RESEARCH_NOTES.md`.
5. If you change the judged demo path, update `docs/QOLLAB_PROJECT_PAGE.md` and `docs/DEMO_SCRIPT.md`.
6. Do not commit API keys, tokens, private notebooks, or generated artifacts.

Suggested ownership:

- Christian: physics assumptions and validation
- Dobromir: Qiskit, inference, active learning, integration
- Alex: baselines, benchmarks, UI, reproducibility
