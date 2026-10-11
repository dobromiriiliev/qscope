from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def plot_history(result, path):
    steps = [item.step for item in result.history]
    confidence = [item.top_location_probability for item in result.history]
    fig, ax = plt.subplots()
    ax.plot(steps, confidence, marker="o")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Top location probability")
    ax.set_ylim(0, 1.02)
    ax.set_title("Q-Scope diagnosis confidence")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_benchmark(summary, path):
    names = list(summary)
    values = [summary[name]["mean_experiments"] for name in names]
    fig, ax = plt.subplots()
    ax.bar(names, values)
    ax.set_ylabel("Mean experiments used")
    ax.set_title("Policy comparison")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
