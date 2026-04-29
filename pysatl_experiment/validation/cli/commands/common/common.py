from pysatl_experiment.cli.commands.common.common import get_project_root, normalize_experiment_name


def if_experiment_exists(name: str) -> bool:
    """
    Check if experiment with the given name exists.
    """
    name = normalize_experiment_name(name)

    experiments_dir = get_project_root() / ".experiments"
    experiment_path = experiments_dir / f"{name}.json"

    return experiment_path.exists()
