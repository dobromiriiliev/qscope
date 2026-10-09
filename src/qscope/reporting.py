from __future__ import annotations

from .hamiltonian import parameter_names


def diagnosis_markdown(result: dict, nominal: list[float], truth: list[float], num_qubits: int) -> str:
    names = parameter_names(num_qubits)
    estimate = result["final_map_vector"]
    lines = [
        "# Q-Scope diagnosis report",
        "",
        f"Strategy: **{result['strategy']}**",
        f"Experiments used: **{len(result['steps'])}**",
        f"Final MAP confidence: **{result['final_map_confidence']:.3f}**",
        "",
        "| Parameter | Nominal | Hidden | Estimate |",
        "|---|---:|---:|---:|",
    ]
    for name, n, t, e in zip(names, nominal, truth, estimate):
        lines.append(f"| {name} | {n:.4f} | {t:.4f} | {e:.4f} |")
    if result["steps"]:
        last = result["steps"][-1]
        lines += [
            "",
            f"Final relative parameter error: **{last['relative_error']:.4f}**",
            f"Drift location correct: **{last['correct_drift_location']}**",
        ]
    return "\n".join(lines) + "\n"
