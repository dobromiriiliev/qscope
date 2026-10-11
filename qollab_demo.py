from pathlib import Path
import sys

root = Path(__file__).resolve().parent
source = root / "src"
if str(source) not in sys.path:
    sys.path.insert(0, str(source))

from qscope.benchmark import run_benchmark, summarize
from qscope.config import load_config
from qscope.factory import build_components, build_engine


cfg = load_config(root / "configs" / "mvp.json")
nominal, hypotheses, experiments, predictions, likelihoods = build_components(cfg)
result = build_engine(
    cfg,
    nominal,
    hypotheses,
    experiments,
    predictions,
    likelihoods,
).run()

print("status:", result.status)
print("location:", result.location)
print("confidence:", round(result.location_probability, 4))
print("delta:", None if result.delta_mean is None else round(result.delta_mean, 4))
print("experiments:", result.experiments_used)

rows = run_benchmark(
    cfg,
    nominal,
    hypotheses,
    experiments,
    predictions,
    likelihoods,
    trials=1,
    output=root / "artifacts" / "qollab_benchmark.csv",
)

print(summarize(rows))
