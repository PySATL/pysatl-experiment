"""Run the time complexity experiment from its example configuration."""

import time
from pathlib import Path

from pysatl_experiment.experiment_execution.build import build_experiment_from_json
from pysatl_experiment.experiment_execution.runner import Experiment


def main() -> None:
    """Build and run the experiment configured in laplace_time_complexity.json."""
    config_path = (
        Path(__file__).resolve().parent / "experiment_example/configs/time_complexity/laplace_time_complexity.json"
    )
    steps = build_experiment_from_json(config_path)
    Experiment(steps).run_experiment()


if __name__ == "__main__":
    start = time.perf_counter()

    # код, время которого измеряем
    main()

    elapsed = time.perf_counter() - start

    print(f"Время выполнения: {elapsed:.6f} сек.")
