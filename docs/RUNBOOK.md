# Runbook

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Tests

```bash
pytest -q
```

## Smoke run

```bash
qscope demo --config configs/smoke.json --output artifacts/smoke.json --plot artifacts/smoke.png
```

## Full package demo

```bash
qscope demo --config configs/mvp.json
```

## Package benchmark

```bash
qscope benchmark --config configs/mvp.json --trials 2
```

## Qollab single-file path

```bash
python -c "import main; main.main()"
```

Expected generated files:

```text
qscope_dashboard.png
qscope_protocol.png
qscope_measurement.png
qscope_offgrid_benchmark.png
qscope_results.json
```

## Submission check

```bash
qscope validate-submission --root .
```
