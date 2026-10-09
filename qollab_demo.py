"""Minimal Qollab-friendly entry point.

Run from repository root after installing requirements:
    python qollab_demo.py
"""

from qscope.config import build_from_config, load_config
from qscope.diagnosis import run_diagnosis

config = load_config("configs/mvp.json")
nominal, hidden, posterior, experiments = build_from_config(config)
settings = config["diagnosis"]

result = run_diagnosis(
    hidden=hidden,
    nominal=nominal,
    posterior=posterior,
    experiments=experiments,
    max_steps=int(settings["max_steps"]),
    strategy="active",
    seed=int(settings["seed"]),
    active_score=settings.get("active_score", "information_gain"),
    repeat_penalty=float(settings.get("repeat_penalty", 0.35)),
    min_steps=int(settings.get("min_steps", 1)),
    stop_map_confidence=settings.get("stop_map_confidence"),
)

for step in result.steps:
    print(
        f"step {step.step:02d} | {step.experiment_name:<28} | "
        f"error={step.relative_error:.4f} | MAP={step.map_confidence:.3f}"
    )

print("\nFinal estimate:", result.final_map_vector)
