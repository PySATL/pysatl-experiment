from pathlib import Path


def if_experiment_exists(name: str) -> bool:
    """
    Check if experiment with the given name exists.
    """

    # pysatl-experiment/.experiments
    experiments_dir = Path(__file__).resolve().parents[5] / ".experiments"
    experiment_file_name = f"{name}.json"

    experiment_path = experiments_dir / experiment_file_name

    return experiment_path.exists()
