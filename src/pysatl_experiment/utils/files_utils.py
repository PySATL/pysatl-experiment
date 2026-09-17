"""Filesystem path helpers for experiment user data."""

from pathlib import Path

from pysatl_experiment.constants import EXPERIMENTS_DIR, RESULTS_DIR, USER_DATA_DIR
from pysatl_experiment.utils.experiment_names import normalize_experiment_name


def ensure_user_data_dir() -> Path:
    """
    Resolve the configured user data directory path.

    Returns
    -------
    Path
        Absolute path to the ``user_data`` directory.
    """
    return Path(USER_DATA_DIR).resolve()


def ensure_experiment_dir() -> Path:
    """
    Build the path to the experiments' directory.

    Ensures the ``.experiments`` directory exists before returning
    the path.

    Returns
    -------
    Path
        Location of the ``.experiments`` directory.
    """
    results_dir = ensure_user_data_dir() / EXPERIMENTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    return results_dir


def ensure_experiment_conf(experiment_name: str) -> Path:
    """
    Build the filesystem path for an experiment JSON file.

    Ensures the ``.experiments`` directory exists before returning
    the path.

    Parameters
    ----------
    experiment_name : str
        Experiment name. The ``.json`` extension is appended
        automatically if missing.

    Returns
    -------
    Path
        Location of the experiment JSON file.
    """
    experiment_name = normalize_experiment_name(experiment_name)

    experiments_dir = ensure_user_data_dir() / EXPERIMENTS_DIR
    experiments_dir.mkdir(parents=True, exist_ok=True)

    experiment_file_name = f"{experiment_name}.json"
    experiment_path = experiments_dir / experiment_file_name
    return experiment_path


def ensure_result_dir() -> Path:
    """
    Build the path to the results' directory.

    Ensures the ``.results`` directory exists before returning
    the path.

    Returns
    -------
    Path
        Location of the ``.results`` directory.
    """
    results_dir = ensure_user_data_dir() / RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    return results_dir
