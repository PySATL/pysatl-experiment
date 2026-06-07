"""
Experiment existence utilities.

This module provides helper functions for checking whether
experiment configuration files already exist in the project
experiment directory.
"""

from src.pysatl_experiment.cli.commands.common import get_project_root, normalize_experiment_name


def if_experiment_exists(name: str) -> bool:
    """
    Check whether an experiment exists.

    Parameters
    ----------
    name : str
        Experiment name.

    Returns
    -------
    bool
        True if the experiment exists, otherwise False.
    """
    name = normalize_experiment_name(name)

    experiments_dir = get_project_root() / ".experiments"
    experiment_path = experiments_dir / f"{name}.json"

    return experiment_path.exists()
