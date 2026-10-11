from __future__ import annotations

import argparse
import importlib
import json
import platform

from qscope.benchmark import run_benchmark, summarize
from qscope.config import load_config
from qscope.factory import build_components, build_engine
from qscope.experiments import build_experiments
from qscope.physics import build_hypotheses, params_from_config
from qscope.io import write_json
from qscope.plotting import plot_benchmark, plot_history
from qscope.submission import validate_submission


def inspect_command(args):
    cfg = load_config(args.config)
    nominal = params_from_config(cfg.model)
    hypotheses = build_hypotheses(nominal, cfg.hypotheses)
    experiments = build_experiments(cfg.experiments)
    print(f"qubits: {nominal.n_qubits}")
    print(f"hypotheses: {len(hypotheses)}")
    print(f"experiments: {len(experiments)}")
    print(f"shots per experiment: {cfg.experiments.shots}")


def preflight_command(args):
    print(f"python: {platform.python_version()}")
    for name in ("qiskit", "numpy", "scipy", "matplotlib"):
        module = importlib.import_module(name)
        print(f"{name}: {getattr(module, '__version__', 'unknown')}")
    print("preflight passed")


def demo_command(args):
    cfg = load_config(args.config)
    nominal, hypotheses, experiments, predictions, likelihoods = build_components(cfg)
    result = build_engine(cfg, nominal, hypotheses, experiments, predictions, likelihoods).run()
    write_json(args.output, result.to_dict())
    plot_history(result, args.plot)
    print(json.dumps(result.to_dict(), indent=2))


def benchmark_command(args):
    cfg = load_config(args.config)
    nominal, hypotheses, experiments, predictions, likelihoods = build_components(cfg)
    rows = run_benchmark(cfg, nominal, hypotheses, experiments, predictions, likelihoods, args.trials, args.output)
    summary = summarize(rows)
    write_json(args.summary, summary)
    plot_benchmark(summary, args.plot)
    print(json.dumps(summary, indent=2))


def validate_command(args):
    failures = validate_submission(args.root)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        raise SystemExit(1)
    print("submission files look complete")


def main():
    parser = argparse.ArgumentParser(prog="qscope")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--config", default="configs/mvp.json")
    inspect_parser.set_defaults(func=inspect_command)

    preflight_parser = sub.add_parser("preflight")
    preflight_parser.set_defaults(func=preflight_command)

    demo_parser = sub.add_parser("demo")
    demo_parser.add_argument("--config", default="configs/mvp.json")
    demo_parser.add_argument("--output", default="artifacts/diagnosis.json")
    demo_parser.add_argument("--plot", default="artifacts/posterior_history.png")
    demo_parser.set_defaults(func=demo_command)

    benchmark_parser = sub.add_parser("benchmark")
    benchmark_parser.add_argument("--config", default="configs/mvp.json")
    benchmark_parser.add_argument("--trials", type=int, default=3)
    benchmark_parser.add_argument("--output", default="artifacts/benchmark_raw.csv")
    benchmark_parser.add_argument("--summary", default="artifacts/benchmark_summary.json")
    benchmark_parser.add_argument("--plot", default="artifacts/benchmark.png")
    benchmark_parser.set_defaults(func=benchmark_command)

    validate_parser = sub.add_parser("validate-submission")
    validate_parser.add_argument("--root", default=".")
    validate_parser.set_defaults(func=validate_command)

    args = parser.parse_args()
    args.func(args)
