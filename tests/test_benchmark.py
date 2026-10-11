from qscope.benchmark import _fixed_schedule, default_scenarios
from qscope.config import load_config
from qscope.experiments import build_experiments


def test_fixed_schedule_spans_experiment_bank():
    cfg = load_config("configs/mvp.json")
    experiments = build_experiments(cfg.experiments)
    schedule = _fixed_schedule(experiments, cfg.stopping.max_experiments)
    assert schedule[0] == 0
    assert schedule[-1] == len(experiments) - 1
    assert len(schedule) == cfg.stopping.max_experiments


def test_default_benchmark_uses_drift_scenarios_only():
    cfg = load_config("configs/mvp.json")
    scenarios = default_scenarios(cfg)
    assert len(scenarios) == 6
    assert all(item.location != "NO_DRIFT" for item in scenarios)


def test_default_benchmark_is_off_grid():
    cfg = load_config("configs/mvp.json")
    scenarios = default_scenarios(cfg)
    assert {item.delta for item in scenarios} == {-0.275, 0.275}
