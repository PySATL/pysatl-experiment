"""Utilities for reading and writing experiment configuration data."""

import json
from pathlib import Path

from line_profiler import profile

from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage, RandomValuesCountQuery
from pysatl_experiment.utils.experiment_names import normalize_experiment_name
from pysatl_experiment.utils.files_utils import ensure_experiment_conf, ensure_experiment_dir


def is_experiment_exists(experiment_name: str) -> bool:
    """
    Check whether an experiment exists.

    Parameters
    ----------
    experiment_name : str
        Experiment name.

    Returns
    -------
    bool
        True if the experiment exists, otherwise False.
    """
    experiment_path = ensure_experiment_dir() / f"{normalize_experiment_name(experiment_name)}.json"

    return experiment_path.exists()


def save_experiment_data(experiment_name: str, experiment_data: dict) -> None:
    """
    Serialize experiment data to a JSON file.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment. Used to determine the output file path.
    experiment_data : dict
        Experiment data to serialize as JSON.
    """
    experiment_path = ensure_experiment_conf(experiment_name)
    with Path.open(experiment_path, "w") as file:
        json.dump(experiment_data, file, indent=4)


def save_experiment_config(experiment_name: str, experiment_config: dict) -> None:
    """
    Update the configuration section of an existing experiment.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment.
    experiment_config : dict
        New configuration dictionary to store.

    Notes
    -----
    Reads the current experiment data, replaces the ``"config"`` section,
    and writes the result back to disk.
    """
    experiment_data = read_experiment_data(experiment_name)
    experiment_data["config"] = experiment_config
    save_experiment_data(experiment_name, experiment_data)


def read_experiment_data(experiment_name: str) -> dict:
    """
    Read experiment data from its JSON file.

    Parameters
    ----------
    experiment_name : str
        Name of the experiment.

    Returns
    -------
    dict
        Experiment data deserialized from JSON.
    """
    experiment_path = ensure_experiment_conf(normalize_experiment_name(experiment_name))
    with Path.open(experiment_path) as file:
        data = json.load(file)

    return dict(data)


@profile
def get_sample_data_from_storage(
    generator_name: str,
    generator_parameters: list[float],
    sample_size: int,
    count: int,
    data_storage: IRandomValuesStorage,
) -> list[list[float]]:
    """
    Load generated samples from storage.

    Parameters
    ----------
    generator_name : str
        Name of the random value generator.
    generator_parameters : list[float]
        Generator parameters used during sample generation.
    sample_size : int
        Size of each generated sample.
    count : int
        Number of samples to load.
    data_storage : IRandomValuesStorage
        Storage backend containing generated random samples.

    Returns
    -------
    list[list[float]]
        Loaded samples.

    Raises
    ------
    ValueError
        If the storage contains fewer samples than requested.
    """
    data = []

    query = RandomValuesCountQuery(
        generator_name=generator_name,
        generator_parameters=generator_parameters,
        sample_size=sample_size,
        count=count,
    )

    data_from_db = data_storage.get_count_data(query)
    if data_from_db is None or len(data_from_db) < count:
        raise ValueError("Not enough data in storage.")

    for sample_data in data_from_db:
        sample = sample_data.data
        data.append(sample)

    return data
