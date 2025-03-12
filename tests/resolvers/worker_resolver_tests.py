from stattest.resolvers.worker_resolver import WorkerResolver


def test_load_power_calculation_worker():
    params = {
        "alpha": 0.05,
        "monte_carlo_count": 100000,
        "cv_store": {
            "name": "CriticalValueDbStore",
            "params": {"db_url": "sqlite:///weibull_experiment.sqlite"},
        },
        "hypothesis": {"name": "WeibullHypothesis"},
    }
    worker = WorkerResolver.load("PowerCalculationWorker", None, params)

    assert worker is not None
