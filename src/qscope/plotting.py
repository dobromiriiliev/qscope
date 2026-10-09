from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .benchmark import summarize_by_step
from .hamiltonian import parameter_names


def plot_benchmark(rows: list[dict], output_path: str | Path) -> None:
    summary = summarize_by_step(rows)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for strategy in sorted({r["strategy"] for r in summary}):
        subset = sorted([r for r in summary if r["strategy"] == strategy], key=lambda r: r["step"])
        steps = [r["step"] for r in subset]
        means = [r["mean_relative_error"] for r in subset]
        stds = [r["std_relative_error"] for r in subset]
        ax.plot(steps, means, marker="o", label=strategy)
        ax.fill_between(
            steps,
            [max(0.0, m - s) for m, s in zip(means, stds)],
            [m + s for m, s in zip(means, stds)],
            alpha=0.15,
        )
    ax.set_xlabel("Experiment number")
    ax.set_ylabel("Relative parameter error")
    ax.set_title("Hamiltonian reconstruction error")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=180)
    plt.close(fig)


def plot_final_parameters(
    nominal: list[float],
    truth: list[float],
    estimate: list[float],
    num_qubits: int,
    output_path: str | Path,
) -> None:
    names = parameter_names(num_qubits)
    x = list(range(len(names)))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([v - width for v in x], nominal, width=width, label="nominal")
    ax.bar(x, truth, width=width, label="hidden")
    ax.bar([v + width for v in x], estimate, width=width, label="estimate")
    ax.set_xticks(x, names)
    ax.set_ylabel("Parameter value")
    ax.set_title("Nominal vs hidden vs reconstructed Hamiltonian")
    ax.legend()
    fig.tight_layout()
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=180)
    plt.close(fig)
