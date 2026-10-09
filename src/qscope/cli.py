from __future__ import annotations

import argparse
from pathlib import Path

from .benchmark import benchmark_headline, benchmark_strategies, summarize_by_step
from .config import build_from_config, load_config
from .diagnosis import run_diagnosis
from .experiments import summarize_experiment_space
from .io import write_json, write_rows_csv
from .plotting import plot_benchmark, plot_final_parameters
from .reporting import diagnosis_markdown
from .submission import checks_passed, validate_repository


def _artifact_dir(config: dict) -> Path:
    return Path(config.get("output", {}).get("artifact_dir", "artifacts"))


def cmd_demo(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    nominal, hidden, posterior, experiments = build_from_config(config)
    diag = config["diagnosis"]
    result = run_diagnosis(
        hidden=hidden,
        nominal=nominal,
        posterior=posterior,
        experiments=experiments,
        max_steps=int(diag["max_steps"]),
        strategy=args.strategy or diag.get("strategy", "active"),
        seed=int(args.seed if args.seed is not None else diag.get("seed", 7)),
        active_score=diag.get("active_score", "information_gain"),
        repeat_penalty=float(diag.get("repeat_penalty", 0.35)),
        min_steps=int(diag.get("min_steps", 1)),
        stop_map_confidence=diag.get("stop_map_confidence"),
    )

    for step in result.steps:
        print(
            f"step={step.step:02d}  {step.experiment_name:<28} "
            f"<O>={step.measured_expectation:+.3f}  "
            f"MAP={step.map_confidence:.3f}  err={step.relative_error:.4f}  "
            f"drift={step.detected_drift_index}"
        )

    out = _artifact_dir(config)
    out.mkdir(parents=True, exist_ok=True)
    result_dict = result.to_dict()
    write_json(result_dict, out / "demo_result.json")
    (out / "demo_report.md").write_text(
        diagnosis_markdown(
            result_dict,
            nominal.as_vector().tolist(),
            hidden.as_vector().tolist(),
            nominal.num_qubits,
        ),
        encoding="utf-8",
    )
    plot_final_parameters(
        nominal.as_vector().tolist(),
        hidden.as_vector().tolist(),
        result.final_map_vector,
        nominal.num_qubits,
        out / "demo_parameters.png",
    )
    print(f"\nWrote {out / 'demo_result.json'}")
    print(f"Wrote {out / 'demo_report.md'}")
    print(f"Wrote {out / 'demo_parameters.png'}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    nominal, hidden, posterior, experiments = build_from_config(config)
    diag = config["diagnosis"]
    bench = config["benchmark"]
    trials = int(args.trials if args.trials is not None else bench.get("trials", 8))
    strategies = tuple(bench.get("strategies", ["active", "random", "fixed"]))
    rows = benchmark_strategies(
        hidden=hidden,
        nominal=nominal,
        base_posterior=posterior,
        experiments=experiments,
        max_steps=int(diag["max_steps"]),
        trials=trials,
        seed=int(diag.get("seed", 7)),
        strategies=strategies,
        active_score=diag.get("active_score", "information_gain"),
        repeat_penalty=float(diag.get("repeat_penalty", 0.35)),
    )
    target = float(bench.get("target_relative_error", 0.08))
    summary = summarize_by_step(rows)
    headline = benchmark_headline(rows, target)
    out = _artifact_dir(config)
    out.mkdir(parents=True, exist_ok=True)
    write_rows_csv(rows, out / "benchmark_raw.csv")
    write_rows_csv(summary, out / "benchmark_summary.csv")
    write_json(headline, out / "benchmark_headline.json")
    plot_benchmark(rows, out / "benchmark.png")
    print(f"Wrote {out / 'benchmark_raw.csv'}")
    print(f"Wrote {out / 'benchmark_summary.csv'}")
    print(f"Wrote {out / 'benchmark_headline.json'}")
    print(f"Wrote {out / 'benchmark.png'}")
    print("\nHeadline metrics:")
    for strategy, metrics in headline.items():
        print(f"  {strategy}: {metrics}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    nominal, hidden, posterior, experiments = build_from_config(config)
    print(f"qubits: {nominal.num_qubits}")
    print(f"nominal: {nominal.to_dict()}")
    print(f"hidden:  {hidden.to_dict()}")
    print(f"particles: {len(posterior.particles)}")
    print(f"experiment space: {summarize_experiment_space(experiments)}")
    print("first experiments:")
    for exp in experiments[: min(10, len(experiments))]:
        print(f"  - {exp.label}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    checks = validate_repository(args.root)
    for check in checks:
        mark = "PASS" if check.passed else "FAIL"
        print(f"[{mark}] {check.name}: {check.detail}")
    return 0 if checks_passed(checks) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qscope", description="Q-Scope hackathon toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run one diagnosis")
    demo.add_argument("--config", default="configs/mvp.json")
    demo.add_argument("--strategy", choices=["active", "random", "fixed"], default=None)
    demo.add_argument("--seed", type=int, default=None)
    demo.set_defaults(func=cmd_demo)

    benchmark = sub.add_parser("benchmark", help="compare active/random/fixed strategies")
    benchmark.add_argument("--config", default="configs/mvp.json")
    benchmark.add_argument("--trials", type=int, default=None)
    benchmark.set_defaults(func=cmd_benchmark)

    inspect = sub.add_parser("inspect", help="inspect config, prior, and experiment space")
    inspect.add_argument("--config", default="configs/mvp.json")
    inspect.set_defaults(func=cmd_inspect)

    validate = sub.add_parser("validate-submission", help="check common hackathon submission requirements")
    validate.add_argument("--root", default=".")
    validate.set_defaults(func=cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
