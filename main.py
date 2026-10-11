from dataclasses import dataclass
from math import lgamma
from pathlib import Path
import json
import warnings

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Circle, FancyBboxPatch
import numpy as np
from scipy.special import logsumexp
from scipy.sparse import SparseEfficiencyWarning

from qiskit import QuantumCircuit
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.synthesis import MatrixExponential

warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)

N_QUBITS = 4
J_NOMINAL = (1.0, 1.0, 1.0)
H_FIELDS = (0.5, 0.5, 0.5, 0.5)
STATES = ("0000", "++++")
TIMES = (0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5)
OBSERVABLES = ("ZZ_01", "ZZ_12", "ZZ_23", "X_0", "X_1", "X_2", "X_3")
LOCATIONS = ("ZZ_01", "ZZ_12", "ZZ_23")
SHOTS = 128
MAX_STEPS = 15
SWITCH_CONFIDENCE = 0.90
STOP_CONFIDENCE = 0.98
DELTA_WIDTH = 0.05
TRUE_LOCATION = "ZZ_23"
TRUE_DELTA = -0.35
SEED = 42
BENCHMARK_SEEDS = (101, 202)
OFF_GRID_DELTAS = (-0.275, 0.275)
BENCHMARK_SCENARIOS = tuple((loc, delta) for loc in LOCATIONS for delta in OFF_GRID_DELTAS)

BG = "#0b1017"
PANEL = "#121923"
PANEL_2 = "#17212d"
TEXT = "#f4f7fb"
MUTED = "#9aa7b5"
GRID = "#263445"
CYAN = "#46c8ff"
VIOLET = "#9b8cff"
GREEN = "#5bd6a2"
AMBER = "#ffb85c"
RED = "#ff6f7d"
LOCATION_COLORS = {"ZZ_01": CYAN, "ZZ_12": VIOLET, "ZZ_23": GREEN}


@dataclass(frozen=True)
class Hypothesis:
    location: str
    delta: float
    J: tuple[float, float, float]


@dataclass(frozen=True)
class Experiment:
    state: str
    time: float
    observable: str


def hamiltonian(J):
    terms = [("ZZ", [i, i + 1], J[i]) for i in range(3)]
    terms.extend(("X", [i], H_FIELDS[i]) for i in range(N_QUBITS))
    return SparsePauliOp.from_sparse_list(terms, num_qubits=N_QUBITS).simplify()


def drifted_J(location, delta):
    values = list(J_NOMINAL)
    values[int(location[-2])] += delta
    return tuple(values)


def make_hypotheses():
    grid = np.round(np.arange(-0.50, 0.501, 0.05), 10)
    deltas = [float(x) for x in grid if abs(x) > 1e-12]
    return [Hypothesis(loc, d, drifted_J(loc, d)) for loc in LOCATIONS for d in deltas]


def make_experiments():
    return [Experiment(state, time, obs) for state in STATES for time in TIMES for obs in OBSERVABLES]


def initial_state(name):
    qc = QuantumCircuit(N_QUBITS)
    for qubit, symbol in enumerate(reversed(name)):
        if symbol == "1":
            qc.x(qubit)
        elif symbol == "+":
            qc.h(qubit)
        elif symbol == "-":
            qc.x(qubit)
            qc.h(qubit)
        elif symbol != "0":
            raise ValueError(f"unsupported state symbol: {symbol}")
    return Statevector.from_instruction(qc)


def observable(name):
    if name.startswith("ZZ_"):
        i, j = int(name[-2]), int(name[-1])
        term = ("ZZ", [i, j], 1.0)
    elif name.startswith("X_"):
        term = ("X", [int(name[-1])], 1.0)
    else:
        raise ValueError(name)
    return SparsePauliOp.from_sparse_list([term], num_qubits=N_QUBITS)


def basis_rotation(name):
    qc = QuantumCircuit(N_QUBITS)
    if name.startswith("X_"):
        qc.h(int(name[-1]))
    return qc


def measured_qubits(name):
    if name.startswith("ZZ_"):
        return int(name[-2]), int(name[-1])
    return (int(name[-1]),)


class Predictor:
    def __init__(self):
        self._states = {}
        self._operators = {name: observable(name) for name in OBSERVABLES}

    def state(self, J, state_name, time):
        key = (J, state_name, float(time))
        if key not in self._states:
            gate = PauliEvolutionGate(
                hamiltonian(J),
                time=float(time),
                synthesis=MatrixExponential(),
            )
            self._states[key] = initial_state(state_name).evolve(gate)
        return self._states[key]

    def p_plus(self, J, experiment):
        state = self.state(J, experiment.state, experiment.time)
        mu = float(np.real(state.expectation_value(self._operators[experiment.observable])))
        return float(np.clip((1.0 + mu) / 2.0, 1e-12, 1.0 - 1e-12))

    def sample(self, J, experiment, shots, seed):
        state = self.state(J, experiment.state, experiment.time).evolve(basis_rotation(experiment.observable))
        state.seed(seed)
        counts = state.sample_counts(shots)
        qubits = measured_qubits(experiment.observable)
        plus = 0
        for bitstring, count in counts.items():
            bits = str(bitstring).replace(" ", "")[::-1]
            parity = sum(int(bits[q]) for q in qubits) % 2
            if parity == 0:
                plus += int(count)
        return plus, {str(k): int(v) for k, v in counts.items()}


def prediction_cache(hypotheses, experiments, predictor):
    values = np.empty((len(hypotheses), len(experiments)), dtype=float)
    for h, hypothesis in enumerate(hypotheses):
        for e, experiment in enumerate(experiments):
            values[h, e] = predictor.p_plus(hypothesis.J, experiment)
    return values


def likelihood_cache(predictions):
    k = np.arange(SHOTS + 1, dtype=float)
    log_choose = np.array([
        lgamma(SHOTS + 1) - lgamma(i + 1) - lgamma(SHOTS - i + 1)
        for i in range(SHOTS + 1)
    ])
    log_tables = []
    prob_tables = []
    for e in range(predictions.shape[1]):
        p = predictions[:, e][:, None]
        logpmf = (
            log_choose[None, :]
            + k[None, :] * np.log(p)
            + (SHOTS - k)[None, :] * np.log1p(-p)
        )
        log_tables.append(logpmf)
        prob_tables.append(np.exp(logpmf))
    return prob_tables, log_tables


def entropy(values, axis=None):
    values = np.asarray(values, dtype=float)
    terms = np.zeros_like(values)
    mask = values > 0
    terms[mask] = values[mask] * np.log(values[mask])
    return -np.sum(terms, axis=axis)


def location_indices(hypotheses):
    return {
        loc: np.array([i for i, h in enumerate(hypotheses) if h.location == loc], dtype=int)
        for loc in LOCATIONS
    }


def location_posterior(weights, indices):
    return {loc: float(weights[idx].sum()) for loc, idx in indices.items()}


def update(weights, log_table, plus_count):
    log_weights = np.log(np.clip(weights, 1e-300, 1.0)) + log_table[:, plus_count]
    log_weights -= logsumexp(log_weights)
    return np.exp(log_weights)


def location_information_gain(weights, likelihoods, indices):
    current = np.array(list(location_posterior(weights, indices).values()))
    current_entropy = entropy(current)
    membership = np.zeros((len(LOCATIONS), len(weights)), dtype=float)
    for row, loc in enumerate(LOCATIONS):
        membership[row, indices[loc]] = 1.0
    scores = np.zeros(len(likelihoods), dtype=float)
    for e, pmf in enumerate(likelihoods):
        predictive = weights @ pmf
        joint = weights[:, None] * pmf
        posterior = np.divide(
            joint,
            predictive[None, :],
            out=np.zeros_like(joint),
            where=predictive[None, :] > 0,
        )
        location_given_count = membership @ posterior
        scores[e] = current_entropy - float(predictive @ entropy(location_given_count, axis=0))
    return scores


def delta_information_gain(weights, likelihoods, idx):
    local = weights[idx]
    local = local / local.sum()
    current_entropy = entropy(local)
    scores = np.zeros(len(likelihoods), dtype=float)
    for e, full_pmf in enumerate(likelihoods):
        pmf = full_pmf[idx, :]
        predictive = local @ pmf
        joint = local[:, None] * pmf
        posterior = np.divide(
            joint,
            predictive[None, :],
            out=np.zeros_like(joint),
            where=predictive[None, :] > 0,
        )
        scores[e] = current_entropy - float(predictive @ entropy(posterior, axis=0))
    return scores


def delta_summary(hypotheses, weights, idx):
    values = np.array([hypotheses[i].delta for i in idx], dtype=float)
    local = weights[idx]
    local = local / local.sum()
    mean = float(local @ values)
    order = np.argsort(values)
    values = values[order]
    local = local[order]
    cumulative = np.cumsum(local)
    low = float(values[min(np.searchsorted(cumulative, 0.05), len(values) - 1)])
    high = float(values[min(np.searchsorted(cumulative, 0.95), len(values) - 1)])
    return mean, low, high


def select_experiment(weights, hypotheses, experiments, predictions, likelihoods, indices):
    locations = location_posterior(weights, indices)
    top = max(locations, key=locations.get)
    confidence = locations[top]
    if confidence >= SWITCH_CONFIDENCE:
        scores = delta_information_gain(weights, likelihoods, indices[top])
        mode = "CALIBRATE"
    else:
        scores = location_information_gain(weights, likelihoods, indices)
        mode = "LOCALIZE"
    experiment_id = int(np.argmax(scores))
    experiment = experiments[experiment_id]
    ranked = sorted(locations.items(), key=lambda item: item[1], reverse=True)
    if mode == "LOCALIZE":
        a, b = ranked[:2]
        means = []
        for loc, _ in (a, b):
            idx = indices[loc]
            local = weights[idx] / weights[idx].sum()
            p = float(local @ predictions[idx, experiment_id])
            means.append(2.0 * p - 1.0)
        detail = f"{a[0]} vs {b[0]} separation {abs(means[0] - means[1]):.3f}"
    else:
        detail = f"refining {top} magnitude"
    return experiment_id, mode, float(scores[experiment_id]), detail


def diagnose(
    true_location,
    true_delta, 
    hypotheses,
    experiments,
    predictions,
    likelihoods,
    log_likelihoods,
    predictor,
    policy="active",
    seed=SEED,
):
    indices = location_indices(hypotheses)
    weights = np.full(len(hypotheses), 1.0 / len(hypotheses), dtype=float)
    true_J = drifted_J(true_location, true_delta)
    rng = np.random.default_rng(seed)
    fixed_schedule = np.unique(np.linspace(0, len(experiments) - 1, MAX_STEPS, dtype=int))
    history = []
    converged = False

    for step in range(1, MAX_STEPS + 1):
        locations = location_posterior(weights, indices)
        top = max(locations, key=locations.get)
        confidence = locations[top]

        if policy == "active":
            experiment_id, mode, score, detail = select_experiment(
                weights, hypotheses, experiments, predictions, likelihoods, indices
            )
        elif policy == "random":
            experiment_id = int(rng.integers(0, len(experiments)))
            mode, score, detail = "RANDOM", 0.0, "uniform random choice"
        else:
            experiment_id = int(fixed_schedule[(step - 1) % len(fixed_schedule)])
            mode, score, detail = "FIXED", 0.0, "predefined measurement schedule"

        experiment = experiments[experiment_id]
        plus, counts = predictor.sample(true_J, experiment, SHOTS, seed + step)
        weights = update(weights, log_likelihoods[experiment_id], plus)

        locations = location_posterior(weights, indices)
        top = max(locations, key=locations.get)
        confidence = locations[top]
        mean, low, high = delta_summary(hypotheses, weights, indices[top])

        history.append({
            "step": step,
            "mode": mode,
            "experiment_id": experiment_id,
            "state": experiment.state,
            "time": experiment.time,
            "observable": experiment.observable,
            "score": score,
            "detail": detail,
            "plus": plus,
            "minus": SHOTS - plus,
            "counts": counts,
            "locations": locations.copy(),
            "location": top,
            "confidence": confidence,
            "delta": mean,
            "low": low,
            "high": high,
        })

        if confidence >= STOP_CONFIDENCE and high - low <= DELTA_WIDTH:
            converged = True
            break

    final = history[-1]
    return {
        "location": final["location"],
        "confidence": final["confidence"],
        "delta": final["delta"],
        "low": final["low"],
        "high": final["high"],
        "experiments": len(history),
        "shots": len(history) * SHOTS,
        "converged": converged,
        "history": history,
        "weights": weights,
        "true_location": true_location,
        "true_delta": true_delta,
    }


def benchmark(hypotheses, experiments, predictions, likelihoods, log_likelihoods, predictor):
    rows = []
    for scenario_id, (location, delta) in enumerate(BENCHMARK_SCENARIOS):
        for seed in BENCHMARK_SEEDS:
            for policy in ("active", "random", "fixed"):
                result = diagnose(
                    location,
                    delta,
                    hypotheses,
                    experiments,
                    predictions,
                    likelihoods,
                    log_likelihoods,
                    predictor,
                    policy=policy,
                    seed=seed + 1000 * scenario_id,
                )
                success = (
                    result["converged"]
                    and result["location"] == location
                    and abs(result["delta"] - delta) <= 0.075
                )
                rows.append({
                    "policy": policy,
                    "location": location,
                    "true_delta": delta,
                    "success": bool(success),
                    "experiments": result["experiments"],
                    "error": abs(result["delta"] - delta),
                    "interval_covers_truth": bool(result["low"] <= delta <= result["high"]),
                })

    summary = {}
    for policy in ("active", "random", "fixed"):
        selected = [row for row in rows if row["policy"] == policy]
        summary[policy] = {
            "success_rate": float(np.mean([row["success"] for row in selected])),
            "mean_experiments": float(np.mean([row["experiments"] for row in selected])),
            "mean_error": float(np.mean([row["error"] for row in selected])),
            "coverage_rate": float(np.mean([row["interval_covers_truth"] for row in selected])),
            "std_experiments": float(np.std([row["experiments"] for row in selected], ddof=0)),
            "std_error": float(np.std([row["error"] for row in selected], ddof=0)),
            "n": len(selected),
        }
    return rows, summary


def panel(ax):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.9)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(TEXT)


def draw_system(ax, result):
    panel(ax)
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(-0.75, 0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Hamiltonian map", loc="left", fontsize=12, fontweight="bold", pad=12, color=TEXT)

    detected = result["location"]
    for i in range(3):
        loc = f"ZZ_{i}{i+1}"
        color = GREEN if loc == detected else GRID
        width = 5.0 if loc == detected else 2.4
        ax.plot([i + 0.13, i + 0.87], [0, 0], color=color, lw=width, solid_capstyle="round", zorder=1)
        ax.text(i + 0.5, -0.27, f"J{i}{i+1}", color=color if loc == detected else MUTED,
                ha="center", va="center", fontsize=10, fontweight="bold" if loc == detected else "normal")

    for i in range(4):
        ax.add_patch(Circle((i, 0), 0.13, facecolor=PANEL_2, edgecolor=CYAN, linewidth=2.2, zorder=2))
        ax.text(i, 0, f"q{i}", color=TEXT, ha="center", va="center", fontsize=9, fontweight="bold", zorder=3)

    idx = int(detected[-2])
    nominal = J_NOMINAL[idx]
    estimate = nominal + result["delta"]
    ax.text(0, 0.60, "Nominal TFIM", color=MUTED, fontsize=9, ha="left")
    ax.text(0, 0.39, r"$H=\sum J_i Z_iZ_{i+1}+\sum h_iX_i$", color=TEXT, fontsize=12, ha="left")
    ax.text(3.45, 0.60, "Detected drift", color=MUTED, fontsize=9, ha="right")
    ax.text(3.45, 0.36, f"J{idx}{idx+1}: {nominal:.2f}  →  {estimate:.3f}", color=GREEN,
            fontsize=13, fontweight="bold", ha="right")


def draw_summary(ax, result):
    ax.set_facecolor(PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.06, 0.88, "DIAGNOSIS", color=MUTED, fontsize=9, fontweight="bold")
    ax.text(0.06, 0.69, result["location"].replace("ZZ_", "J"), color=GREEN, fontsize=29, fontweight="bold")
    ax.text(0.06, 0.56, "interaction drift", color=TEXT, fontsize=11)

    items = [
        ("Confidence", f"{100 * result['confidence']:.1f}%"),
        ("Estimated δ", f"{result['delta']:+.3f}"),
        ("90% interval", f"[{result['low']:+.2f}, {result['high']:+.2f}]"),
        ("Experiments", str(result["experiments"])),
    ]
    y = 0.40
    for label, value in items:
        ax.text(0.06, y, label, color=MUTED, fontsize=8.5)
        ax.text(0.94, y, value, color=TEXT, fontsize=10.5, fontweight="bold", ha="right")
        y -= 0.10


def draw_location_history(ax, result):
    panel(ax)
    history = result["history"]
    observed_steps = np.array([item["step"] for item in history], dtype=float)
    steps = np.concatenate(([0.0], observed_steps))
    prior = 1.0 / len(LOCATIONS)

    offsets = {"ZZ_01": -0.035, "ZZ_12": 0.0, "ZZ_23": 0.035}
    markers = {"ZZ_01": "s", "ZZ_12": "D", "ZZ_23": "o"}
    linestyles = {"ZZ_01": "--", "ZZ_12": ":", "ZZ_23": "-"}

    first_calibrate = next(
        (item["step"] for item in history if item["mode"] == "CALIBRATE"),
        None,
    )
    if first_calibrate is not None:
        ax.axvspan(
            first_calibrate - 0.5,
            observed_steps[-1] + 0.45,
            color=VIOLET,
            alpha=0.055,
            lw=0,
            zorder=0,
        )
        ax.text(
            first_calibrate + 0.04,
            0.075,
            "calibration",
            color=VIOLET,
            fontsize=7.8,
            fontweight="bold",
            ha="left",
            va="bottom",
        )

    for loc in LOCATIONS:
        values = [prior] + [item["locations"][loc] for item in history]
        shifted_steps = steps + offsets[loc]
        ax.plot(
            shifted_steps,
            values,
            color=LOCATION_COLORS[loc],
            lw=2.35,
            ls=linestyles[loc],
            marker=markers[loc],
            ms=6.2,
            mec=PANEL,
            mew=1.0,
            mfc=LOCATION_COLORS[loc],
            label=loc.replace("ZZ_", "J"),
            zorder=3,
        )

    ax.axhline(STOP_CONFIDENCE, color=MUTED, lw=1, ls="--", alpha=0.55, zorder=1)
    ax.set_ylim(-0.025, 1.03)
    ax.set_xlim(-0.20, max(observed_steps[-1] + 0.38, 2.35))
    ax.set_xticks(steps)
    ax.set_xticklabels(["prior"] + [str(int(x)) for x in observed_steps])
    ax.set_xlabel("Adaptive experiment")
    ax.set_ylabel("Posterior probability")
    ax.set_title("Fault localization", loc="left", fontsize=12, fontweight="bold", pad=10, color=TEXT)
    ax.grid(axis="y", color=GRID, alpha=0.45, linewidth=0.7)

    final_locations = history[-1]["locations"]
    label_text = "   ".join(
        f"{loc.replace('ZZ_', 'J')} {100 * final_locations[loc]:.1f}%"
        for loc in LOCATIONS
    )
    ax.text(
        0.99,
        0.965,
        label_text,
        transform=ax.transAxes,
        color=MUTED,
        fontsize=7.3,
        ha="right",
        va="top",
    )

    legend = ax.legend(frameon=False, labelcolor=TEXT, fontsize=8, ncol=3, loc="lower right")
    for handle in legend.legend_handles:
        handle.set_linewidth(2.4)


def draw_delta_posterior(ax, result, hypotheses):
    panel(ax)
    idx = np.array([i for i, h in enumerate(hypotheses) if h.location == result["location"]], dtype=int)
    values = np.array([hypotheses[i].delta for i in idx], dtype=float)
    weights = result["weights"][idx].astype(float)
    weights = weights / weights.sum()
    order = np.argsort(values)
    values, weights = values[order], weights[order]

    mean = float(result["delta"])
    truth = float(result["true_delta"])
    low = float(result["low"])
    high = float(result["high"])

    ax.bar(
        values,
        weights,
        width=0.039,
        color=GREEN,
        alpha=0.90,
        edgecolor=PANEL,
        linewidth=0.65,
        zorder=2,
    )
    ax.axvspan(low, high, color=CYAN, alpha=0.09, lw=0, zorder=1)
    ax.axvline(mean, color=TEXT, lw=3.0, zorder=5)
    ax.axvline(truth, color=AMBER, lw=2.3, ls=(0, (4, 2)), zorder=6)

    ymax = max(float(np.max(weights)), 0.05)
    close = abs(mean - truth) < 0.012
    mean_marker_x = mean - 0.007 if close else mean
    truth_marker_x = truth + 0.007 if close else truth

    ax.scatter(
        [mean_marker_x],
        [ymax * 1.025],
        marker="D",
        s=45,
        color=TEXT,
        edgecolor=PANEL,
        linewidth=0.8,
        zorder=8,
        clip_on=False,
    )
    ax.scatter(
        [truth_marker_x],
        [ymax * 0.955],
        marker="v",
        s=58,
        color=AMBER,
        edgecolor=PANEL,
        linewidth=0.8,
        zorder=8,
        clip_on=False,
    )

    ax.text(
        0.96,
        0.92,
        f"90% interval   [{low:+.2f}, {high:+.2f}]",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=7.5,
        ha="right",
        va="top",
    )
    ax.text(
        0.96,
        0.82,
        f"◆  posterior mean   {mean:+.3f}",
        transform=ax.transAxes,
        color=TEXT,
        fontsize=8.0,
        fontweight="bold",
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.32", facecolor=PANEL_2, edgecolor=GRID, linewidth=0.7, alpha=0.95),
    )
    ax.text(
        0.96,
        0.70,
        f"▼  injected truth   {truth:+.3f}",
        transform=ax.transAxes,
        color=AMBER,
        fontsize=8.0,
        fontweight="bold",
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.32", facecolor=PANEL_2, edgecolor=GRID, linewidth=0.7, alpha=0.95),
    )

    ax.set_xlim(-0.53, 0.53)
    ax.set_ylim(0, ymax * 1.12)
    ax.set_xlabel("Drift δ")
    ax.set_ylabel("Posterior mass")
    ax.set_title("Magnitude calibration", loc="left", fontsize=12, fontweight="bold", pad=10, color=TEXT)
    ax.grid(axis="y", color=GRID, alpha=0.4, linewidth=0.7)

def draw_benchmark(ax, summary):
    panel(ax)
    names = ("active", "random", "fixed")
    labels = ("Q-Scope", "Random", "Fixed")
    values = [summary[name]["mean_experiments"] for name in names]
    colors = (GREEN, VIOLET, CYAN)
    errors = [summary[name]["std_experiments"] for name in names]
    bars = ax.bar(
        labels, values, yerr=errors, capsize=3.5, color=colors, width=0.62, alpha=0.92,
        error_kw={"ecolor": TEXT, "elinewidth": 1.0, "capthick": 1.0},
    )
    ax.set_ylim(0, MAX_STEPS + 2.5)
    ax.set_ylabel("Mean experiments")
    ax.set_title("Off-grid benchmark", loc="left", fontsize=12, fontweight="bold", pad=10, color=TEXT)
    ax.text(0.98, 0.97, "δ = ±0.275", transform=ax.transAxes,
            color=MUTED, fontsize=7.6, va="top", ha="right")
    ax.grid(axis="y", color=GRID, alpha=0.4, linewidth=0.7)
    for bar, name in zip(bars, names):
        rate = 100 * summary[name]["success_rate"]
        error = summary[name]["mean_error"]
        y = max(0.9, bar.get_height() * 0.78)
        ax.text(bar.get_x() + bar.get_width() / 2, y,
                f"{rate:.0f}% success\nMAE {error:.3f}", color=TEXT, fontsize=7.6,
                ha="center", va="center", fontweight="bold")


def make_dashboard(result, hypotheses, summary, path="qscope_dashboard.png"):
    fig = plt.figure(figsize=(15.5, 8.8), facecolor=BG)
    gs = GridSpec(2, 3, figure=fig, height_ratios=(0.82, 1.35), width_ratios=(1.5, 1.0, 1.0), hspace=0.24, wspace=0.18)
    ax_system = fig.add_subplot(gs[0, :2])
    ax_summary = fig.add_subplot(gs[0, 2])
    ax_location = fig.add_subplot(gs[1, 0])
    ax_delta = fig.add_subplot(gs[1, 1])
    ax_bench = fig.add_subplot(gs[1, 2])

    draw_system(ax_system, result)
    draw_summary(ax_summary, result)
    draw_location_history(ax_location, result)
    draw_delta_posterior(ax_delta, result, hypotheses)
    draw_benchmark(ax_bench, summary)

    fig.text(0.035, 0.975, "Q-SCOPE", color=TEXT, fontsize=22, fontweight="bold", va="top")
    fig.text(0.035, 0.943, "Adaptive diagnosis of a drifting quantum model", color=MUTED, fontsize=10.5, va="top")
    fig.text(0.965, 0.972,
             f"{len(hypotheses)} hypotheses  •  {SHOTS} shots / round  •  {len(BENCHMARK_SCENARIOS) * len(BENCHMARK_SEEDS)} paired cases / policy",
             color=MUTED, fontsize=8.3, ha="right", va="top")
    fig.text(0.965, 0.945, "off-grid truths: δ = ±0.275", color=MUTED, fontsize=8.3, ha="right", va="top")
    fig.text(0.035, 0.015,
             "Off-grid test: the hidden drift is halfway between candidate grid values. All policies use the same experiment bank, shot budget, stopping rule, and round cap.",
             color=MUTED, fontsize=7.8, va="bottom")
    fig.savefig(path, dpi=190, facecolor=BG, bbox_inches="tight", pad_inches=0.28)
    plt.close(fig)


def make_protocol(result, path="qscope_protocol.png"):
    history = result["history"]
    fig, ax = plt.subplots(figsize=(15.5, 4.4), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.91, "Experiment sequence", color=TEXT, fontsize=18, fontweight="bold")
    ax.text(0.03, 0.84, "Q-Scope chooses the next measurement from the current posterior.", color=MUTED, fontsize=9.5)

    n = len(history)
    xs = np.linspace(0.07, 0.93, n)
    y = 0.47
    if n > 1:
        ax.plot([xs[0], xs[-1]], [y, y], color=GRID, lw=2.2, zorder=0)

    for x, item in zip(xs, history):
        color = CYAN if item["mode"] == "LOCALIZE" else VIOLET
        ax.add_patch(Circle((x, y), 0.022, facecolor=color, edgecolor=BG, linewidth=2, zorder=3))
        width = min(0.13, 0.82 / max(n, 1))
        box = FancyBboxPatch(
            (x - width / 2, y - 0.28), width, 0.20,
            boxstyle="round,pad=0.012,rounding_size=0.012",
            facecolor=PANEL, edgecolor=GRID, linewidth=0.8,
        )
        ax.add_patch(box)
        ax.text(x, y + 0.075, f"{item['step']}", color=TEXT, fontsize=9, ha="center", fontweight="bold")
        ax.text(x, y - 0.125, item["observable"].replace("_", ""), color=TEXT, fontsize=8.5, ha="center", fontweight="bold")
        ax.text(x, y - 0.175, f"t={item['time']:g}  |{item['state']}⟩", color=MUTED, fontsize=7.5, ha="center")
        ax.text(x, y - 0.225, f"{100 * item['confidence']:.1f}%", color=color, fontsize=7.8, ha="center", fontweight="bold")

    ax.text(0.03, 0.08, "LOCALIZE", color=CYAN, fontsize=8.5, fontweight="bold")
    ax.text(0.10, 0.08, "maximize information about which coupling drifted", color=MUTED, fontsize=8.5)
    ax.text(0.55, 0.08, "CALIBRATE", color=VIOLET, fontsize=8.5, fontweight="bold")
    ax.text(0.635, 0.08, "maximize information about the drift magnitude", color=MUTED, fontsize=8.5)

    fig.savefig(path, dpi=190, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def make_measurement_card(result, path="qscope_measurement.png"):
    item = result["history"][-1]
    plus = item["plus"]
    minus = item["minus"]
    fig, ax = plt.subplots(figsize=(8.2, 4.2), facecolor=BG)
    panel(ax)
    bars = ax.bar(["+1", "−1"], [plus, minus], color=(GREEN, RED), width=0.55)
    ymax = max(plus, minus, 1)
    ax.set_ylim(0, ymax * 1.22)
    ax.set_ylabel("Shots")
    ax.set_title(f"Final measurement evidence  •  {item['observable']} at t={item['time']:g}", loc="left", fontsize=12, fontweight="bold", pad=10, color=TEXT)
    ax.grid(axis="y", color=GRID, alpha=0.4, linewidth=0.7)
    for bar, value in zip(bars, (plus, minus)):
        ax.text(bar.get_x() + bar.get_width() / 2, value + ymax * 0.035, str(value), color=TEXT, ha="center", fontsize=10, fontweight="bold")

    mode_color = VIOLET if item["mode"] == "CALIBRATE" else CYAN
    ax.text(
        0.79,
        0.925,
        item["mode"],
        transform=ax.transAxes,
        color=mode_color,
        fontsize=8.8,
        fontweight="bold",
        ha="right",
        va="top",
    )
    ax.text(
        0.80,
        0.925,
        f" •  posterior {100 * item['confidence']:.1f}%",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=8.5,
        ha="left",
        va="top",
    )

    fig.tight_layout()
    fig.savefig(path, dpi=190, facecolor=BG, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)



def make_benchmark_figure(summary, path="qscope_offgrid_benchmark.png"):
    names = ("active", "random", "fixed")
    labels = ("Q-Scope", "Random", "Fixed")
    colors = (GREEN, VIOLET, CYAN)

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), facecolor=BG)
    ax_success, ax_error = axes

    for ax in axes:
        panel(ax)

    success = [100 * summary[name]["success_rate"] for name in names]
    bars = ax_success.bar(labels, success, color=colors, width=0.62, alpha=0.94)
    ax_success.set_ylim(0, 108)
    ax_success.set_ylabel("Successful diagnoses (%)")
    ax_success.set_title("Target reached", loc="left", fontsize=12, fontweight="bold", pad=10, color=TEXT)
    ax_success.grid(axis="y", color=GRID, alpha=0.4, linewidth=0.7)
    for bar, value in zip(bars, success):
        ax_success.text(
            bar.get_x() + bar.get_width() / 2,
            value + 2.0,
            f"{value:.0f}%",
            ha="center",
            va="bottom",
            color=TEXT,
            fontsize=9.5,
            fontweight="bold",
        )

    mae = [summary[name]["mean_error"] for name in names]
    mae_sd = [summary[name]["std_error"] for name in names]
    bars = ax_error.bar(
        labels,
        mae,
        yerr=mae_sd,
        capsize=4,
        color=colors,
        width=0.62,
        alpha=0.94,
        error_kw={"ecolor": TEXT, "elinewidth": 1.1, "capthick": 1.1},
    )
    ax_error.set_ylabel(r"Mean absolute drift error $|\hat{\delta}-\delta|$")
    ax_error.set_title("Parameter accuracy", loc="left", fontsize=12, fontweight="bold", pad=10, color=TEXT)
    ax_error.grid(axis="y", color=GRID, alpha=0.4, linewidth=0.7)

    upper_extent = max(value + err for value, err in zip(mae, mae_sd))
    ax_error.set_ylim(0, max(0.08, upper_extent * 1.22))

    for bar, value, err in zip(bars, mae, mae_sd):
        label_y = value + err + max(0.005, upper_extent * 0.035)
        ax_error.text(
            bar.get_x() + bar.get_width() / 2,
            label_y,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            color=TEXT,
            fontsize=9.2,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.18", facecolor=PANEL, edgecolor="none", alpha=0.92),
            zorder=6,
        )

    fig.text(0.04, 0.965, "Off-grid generalization", color=TEXT, fontsize=18, fontweight="bold", va="top")
    fig.text(
        0.04,
        0.915,
        "True drifts are δ = ±0.275, exactly halfway between adjacent 0.05-spaced hypotheses.",
        color=MUTED,
        fontsize=9.2,
        va="top",
    )
    fig.text(
        0.96,
        0.93,
        f"{len(BENCHMARK_SCENARIOS) * len(BENCHMARK_SEEDS)} paired cases per policy",
        color=MUTED,
        fontsize=8.7,
        ha="right",
        va="top",
    )
    fig.text(
        0.04,
        0.025,
        "Same candidate experiments, shots per round, stopping rule, and 15-round budget for all policies.",
        color=MUTED,
        fontsize=8.2,
        va="bottom",
    )

    fig.subplots_adjust(left=0.075, right=0.975, top=0.78, bottom=0.16, wspace=0.28)
    fig.savefig(path, dpi=190, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

def result_payload(result, summary):
    trace = [
        {
            "step": item["step"],
            "mode": item["mode"],
            "state": item["state"],
            "time": item["time"],
            "observable": item["observable"],
            "location": item["location"],
            "confidence": item["confidence"],
            "delta": item["delta"],
        }
        for item in result["history"]
    ]
    return {
        "hidden_system": {
            "location": result["true_location"],
            "delta": result["true_delta"],
        },
        "diagnosis": {
            "location": result["location"],
            "confidence": result["confidence"],
            "delta": result["delta"],
            "credible_interval_90": [result["low"], result["high"]],
            "experiments": result["experiments"],
            "shots": result["shots"],
            "target_reached": result["converged"],
            "trace": trace,
        },
        "benchmark": {
            "type": "off_grid",
            "truth_deltas": list(OFF_GRID_DELTAS),
            "grid_spacing": 0.05,
            "scenarios": len(BENCHMARK_SCENARIOS),
            "seeds": len(BENCHMARK_SEEDS),
            "summary": summary,
        },
    }


def main():
    print("Q-Scope")
    print("Adaptive diagnosis of a drifting transverse-field Ising model")
    print()

    hypotheses = make_hypotheses()
    experiments = make_experiments()
    predictor = Predictor()

    print(f"{'Model':<14}  {N_QUBITS} qubits, 3 candidate ZZ couplings")
    print(f"{'Hypotheses':<14}  {len(hypotheses)}")
    print(f"{'Measurements':<14}  {len(experiments)} candidate experiments")
    print(f"{'Shots / round':<14}  {SHOTS}")
    print()
    print("Preparing the prediction bank...")

    predictions = prediction_cache(hypotheses, experiments, predictor)
    likelihoods, log_likelihoods = likelihood_cache(predictions)

    print("Running the adaptive diagnosis...")
    result = diagnose(
        TRUE_LOCATION,
        TRUE_DELTA,
        hypotheses,
        experiments,
        predictions,
        likelihoods,
        log_likelihoods,
        predictor,
    )

    print()
    print("Diagnosis")
    print(f"  {'coupling':<18}{result['location']}")
    print(f"  {'drift estimate':<18}{result['delta']:+.3f}")
    print(f"  {'90% interval':<18}[{result['low']:+.2f}, {result['high']:+.2f}]")
    print(f"  {'confidence':<18}{100 * result['confidence']:.2f}%")
    print(f"  {'rounds':<18}{result['experiments']}")
    print(f"  {'shots used':<18}{result['shots']}")
    print(f"  {'stopping target':<18}{'reached' if result['converged'] else 'budget exhausted'}")

    print()
    print("Off-grid benchmark")
    print("  Hidden drift values: -0.275 and +0.275")
    print("  Both lie halfway between adjacent values in the 0.05-spaced hypothesis grid.")
    _, summary = benchmark(
        hypotheses,
        experiments,
        predictions,
        likelihoods,
        log_likelihoods,
        predictor,
    )

    print()
    print(f"  {'policy':<12}{'success':>10}{'rounds ± sd':>16}{'mean |δ error|':>17}{'90% CI cover':>14}")
    print("  " + "-" * 69)
    display_names = {"active": "Q-Scope", "random": "Random", "fixed": "Fixed"}
    for name in ("active", "random", "fixed"):
        values = summary[name]
        print(
            f"  {display_names[name]:<12}"
            f"{100 * values['success_rate']:>9.0f}%"
            f"{values['mean_experiments']:>9.2f} ± {values['std_experiments']:<4.2f}"
            f"{values['mean_error']:>15.3f}"
            f"{100 * values['coverage_rate']:>13.0f}%"
        )

    make_dashboard(result, hypotheses, summary)
    make_protocol(result)
    make_measurement_card(result)
    make_benchmark_figure(summary)

    payload = result_payload(result, summary)
    Path("qscope_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    passed = (
        result["location"] == TRUE_LOCATION
        and abs(result["delta"] - TRUE_DELTA) <= 0.075
        and result["confidence"] >= STOP_CONFIDENCE
    )

    print()
    print(f"Validation: {'PASS' if passed else 'FAIL'}")
    print("Outputs:")
    print("  qscope_dashboard.png")
    print("  qscope_protocol.png")
    print("  qscope_measurement.png")
    print("  qscope_offgrid_benchmark.png")
    print("  qscope_results.json")

