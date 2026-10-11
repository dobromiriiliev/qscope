# Contributing

Keep changes focused and reproducible.

1. Branch from `main`.
2. Create a virtual environment and install the development dependencies.
3. Run `pytest -q`.
4. Run the smoke configuration before changing the full demo.
5. Update the relevant documentation when physics assumptions, thresholds, or benchmark definitions change.
6. Do not commit credentials, local virtual environments, generated caches, or private data.

Useful commands:

```bash
pip install -e '.[dev]'
pytest -q
qscope demo --config configs/smoke.json --output artifacts/smoke.json --plot artifacts/smoke.png
qscope validate-submission --root .
```
