.PHONY: install dev test lint demo benchmark inspect ui validate smoke clean

install:
	python -m pip install -e .

dev:
	python -m pip install -e '.[dev,ui]'

test:
	pytest -q

lint:
	ruff check src tests scripts ui

demo:
	qscope demo --config configs/mvp.json

benchmark:
	qscope benchmark --config configs/mvp.json

inspect:
	qscope inspect --config configs/mvp.json

ui:
	streamlit run ui/app.py

validate:
	qscope validate-submission --root .

smoke:
	python scripts/smoke_test.py

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist *.egg-info
	rm -rf artifacts/*
	touch artifacts/.gitkeep
