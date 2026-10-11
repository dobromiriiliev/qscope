.PHONY: install test smoke demo benchmark qollab validate

install:
	python -m pip install -e '.[dev]'

test:
	pytest -q

smoke:
	qscope demo --config configs/smoke.json --output artifacts/smoke.json --plot artifacts/smoke.png

demo:
	qscope demo --config configs/mvp.json

benchmark:
	qscope benchmark --config configs/mvp.json --trials 2

qollab:
	python scripts/run_qollab.py

validate:
	qscope validate-submission --root .
