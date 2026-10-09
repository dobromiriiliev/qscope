from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st

from qscope.benchmark import benchmark_strategies, summarize_by_step
from qscope.config import build_from_config, load_config
from qscope.diagnosis import run_diagnosis
from qscope.hamiltonian import parameter_names


st.set_page_config(page_title="Q-Scope", layout="wide")
st.title("Q-Scope")
st.caption("Active Hamiltonian learning for quantum diagnostics")

config_path = st.sidebar.text_input("Config", "configs/mvp.json")
strategy = st.sidebar.selectbox("Strategy", ["active", "random", "fixed"], index=0)
seed = st.sidebar.number_input("Seed", min_value=0, value=7, step=1)

try:
    config = load_config(ROOT / config_path)
    nominal, hidden, posterior, experiments = build_from_config(config)
except Exception as exc:
    st.error(f"Could not load config: {exc}")
    st.stop()

names = parameter_names(nominal.num_qubits)

st.subheader("Configured system")
cols = st.columns(3)
cols[0].metric("Qubits", nominal.num_qubits)
cols[1].metric("Candidate experiments", len(experiments))
cols[2].metric("Candidate Hamiltonians", len(posterior.particles))

with st.expander("Hamiltonian parameters"):
    rows = []
    for name, n, h in zip(names, nominal.as_vector(), hidden.as_vector()):
        rows.append({"parameter": name, "nominal": float(n), "hidden": float(h)})
    st.dataframe(rows, use_container_width=True, hide_index=True)

if st.button("Run diagnosis", type="primary"):
    diag = config["diagnosis"]
    with st.spinner("Running Q-Scope..."):
        result = run_diagnosis(
            hidden=hidden,
            nominal=nominal,
            posterior=posterior,
            experiments=experiments,
            max_steps=int(diag["max_steps"]),
            strategy=strategy,
            seed=int(seed),
            active_score=diag.get("active_score", "information_gain"),
            repeat_penalty=float(diag.get("repeat_penalty", 0.35)),
            min_steps=int(diag.get("min_steps", 1)),
            stop_map_confidence=diag.get("stop_map_confidence"),
        )

    final = result.steps[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Experiments", len(result.steps))
    c2.metric("Relative error", f"{final.relative_error:.3f}")
    c3.metric("Drift located", "yes" if final.correct_drift_location else "no")

    st.subheader("Diagnosis trace")
    trace = [
        {
            "step": s.step,
            "experiment": s.experiment_name,
            "measurement": s.measured_expectation,
            "MAP confidence": s.map_confidence,
            "relative error": s.relative_error,
            "detected drift index": s.detected_drift_index,
        }
        for s in result.steps
    ]
    st.dataframe(trace, use_container_width=True, hide_index=True)

    st.subheader("Final parameters")
    estimate_rows = []
    for name, n, h, e, sd in zip(
        names,
        nominal.as_vector(),
        hidden.as_vector(),
        result.final_map_vector,
        result.final_std_vector,
    ):
        estimate_rows.append(
            {
                "parameter": name,
                "nominal": float(n),
                "hidden": float(h),
                "estimate": float(e),
                "posterior std": float(sd),
            }
        )
    st.dataframe(estimate_rows, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Quick benchmark")
trials = st.number_input("Trials", min_value=1, max_value=20, value=3, step=1)
if st.button("Run benchmark"):
    with st.spinner("Comparing active, random, and fixed policies..."):
        rows = benchmark_strategies(
            hidden=hidden,
            nominal=nominal,
            base_posterior=posterior,
            experiments=experiments,
            max_steps=int(config["diagnosis"]["max_steps"]),
            trials=int(trials),
            seed=int(seed),
            active_score=config["diagnosis"].get("active_score", "information_gain"),
            repeat_penalty=float(config["diagnosis"].get("repeat_penalty", 0.35)),
        )
    summary = summarize_by_step(rows)
    frame = pd.DataFrame(summary)
    chart = frame.pivot(index="step", columns="strategy", values="mean_relative_error")
    st.line_chart(chart)
    st.dataframe(frame, use_container_width=True, hide_index=True)
