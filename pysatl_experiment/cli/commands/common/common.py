"""Common utilities for CLI commands and experiment management."""

import json
from enum import Enum
from pathlib import Path
from typing import cast

from click import ClickException, Context
from pysatl_criterion.statistics import (
    AbstractExponentialityGofStatistic,
    AbstractNormalityGofStatistic,
    AbstractWeibullGofStatistic,
)
from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic


# TODO: Split utilities into dedicated modules?


def get_project_root() -> Path:
    """
    Locate the project root directory.

    Searches upward from the current module location until a directory
    containing ``pyproject.toml`` or ``.experiments`` is found.

    Returns
    -------
    Path
        Absolute path to the project root directory.

    Raises
    ------
    RuntimeError
        If the project root cannot be determined.
    """
    experiments_base = Path(__file__).resolve().parents[3]
    for parent in [experiments_base, *experiments_base.parents]:
        if (parent / "pyproject.toml").is_file() or (parent / ".experiments").is_dir():
            return parent

    raise RuntimeError(
        "Cannot determine project root. Expected to find pyproject.toml or .experiments in parent directories."
    )


def normalize_experiment_name(name: str) -> str:
    """
    Strip the ``.json`` extension from an experiment name if present.

    Parameters
    ----------
    name : str
        Experiment name, optionally ending with ``.json``.

    Returns
    -------
    str
        Normalized experiment name without the ``.json`` extension.

    Notes
    -----
    This prevents the 'name.json.json' issue when names are passed with
    or without the extension.
    """
    if name.endswith(".json"):
        return name[:-5]
    return name


def create_experiment_path(name: str) -> Path:
    """
    Build the filesystem path for an experiment JSON file.

    Ensures the ``.experiments`` directory exists before returning
    the path.

    Parameters
    ----------
    name : str
        Experiment name. The ``.json`` extension is appended
        automatically if missing.

    Returns
    -------
    Path
        Location of the experiment JSON file.
    """
    name = normalize_experiment_name(name)

    experiments_dir = get_project_root() / ".experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)

    experiment_file_name = f"{name}.json"
    experiment_path = experiments_dir / experiment_file_name
    return experiment_path


def create_result_path() -> Path:
    """
    Build the path to the results' directory.

    Ensures the ``.results`` directory exists before returning
    the path.

    Returns
    -------
    Path
        Location of the ``.results`` directory.
    """
    results_dir = get_project_root() / ".results"
    results_dir.mkdir(parents=True, exist_ok=True)

    return results_dir


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
    experiment_path = create_experiment_path(experiment_name)
    with Path.open(experiment_path, "w") as file:
        json.dump(experiment_data, file, indent=4)


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
    experiment_path = create_experiment_path(experiment_name)
    with Path.open(experiment_path) as file:
        data = json.load(file)

    return dict(data)


def list_possible_parameter_values(param_type: type[Enum]) -> str:
    """
    Format the members of an enumeration as a comma-separated string.

    Parameters
    ----------
    param_type : type[Enum]
        An enumeration class.

    Returns
    -------
    str
        Comma-separated string of the enumeration's values.
    """
    param_type_values = [item.value for item in param_type]
    param_type_values_str = ", ".join(param_type_values)

    return param_type_values_str


def get_statistics_short_codes_for_hypothesis(hypothesis: str) -> list[str]:
    """
    Get short codes of registered goodness-of-fit statistics.

    Parameters
    ----------
    hypothesis : str
        Hypothesis identifier.

    Returns
    -------
    list[str]
        List of short statistic codes (e.g., ``["KS", "AD"]``).
    """
    hypothesis_to_base_class = {
        "exponential": AbstractExponentialityGofStatistic,
        "normal": AbstractNormalityGofStatistic,
        "weibull": AbstractWeibullGofStatistic,
    }  # TODO: constant (``"exponential"``, ``"normal"``, or ``"weibull"``)??

    base_class = hypothesis_to_base_class[hypothesis]

    if base_class is None:
        raise ClickException(
            f"Unsupported hypothesis: {hypothesis}. Must be ``exponential``, ``normal``, or ``weibull``."
        )

    valid_criteria_types = cast(
        list[type[AbstractGoodnessOfFitStatistic]],
        base_class.__subclasses__(),
    )
    valid_criteria_codes = [cls.code().split("_")[0] for cls in valid_criteria_types]

    return valid_criteria_codes


def get_experiment_data(ctx: Context) -> dict:
    """
    Extract experiment data dictionary from the Click context.

    Parameters
    ----------
    ctx : click.Context
        Click context object.

    Returns
    -------
    dict
        Experiment data dictionary.

    Raises
    ------
    click.ClickException
        If experiment data is missing in the context.
    """
    experiment_data = ctx.obj.get("experiment_data")
    if experiment_data is None:
        raise ClickException("Experiment is not created.")

    return experiment_data


def get_experiment_name(experiment_data: dict) -> str:
    """
    Extract the experiment name from experiment data.

    Parameters
    ----------
    experiment_data : dict
        Experiment data dictionary.

    Returns
    -------
    str
        Experiment name.

    Raises
    ------
    click.ClickException
        If the experiment name is missing.
    """
    experiment_name = experiment_data.get("name")
    if experiment_name is None:
        raise ClickException("Experiment name is not configured.")

    return experiment_name


def get_experiment_config(experiment_data: dict) -> dict:
    """
    Extract the experiment configuration section from a data dictionary.

    Parameters
    ----------
    experiment_data : dict
        Experiment data dictionary.

    Returns
    -------
    dict
        Experiment configuration dictionary.

    Raises
    ------
    click.ClickException
        If the experiment configuration is missing.
    """
    experiment_config = experiment_data.get("config")
    if experiment_config is None:
        raise ClickException("Experiment config is not configured.")

    return experiment_config


def get_experiment_name_and_config(ctx: Context) -> tuple[str, dict]:
    """
    Retrieve experiment name and configuration from context.

    Parameters
    ----------
    ctx : click.Context
        Click context object.

    Returns
    -------
    tuple[str, dict]
        Tuple of experiment name and configuration.

    Raises
    ------
    click.ClickException
        If experiment data, name, or config cannot be resolved.
    """
    experiment_data = get_experiment_data(ctx)
    experiment_name = get_experiment_name(experiment_data)
    experiment_config = get_experiment_config(experiment_data)

    return experiment_name, experiment_config


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


def criteria_from_codes(codes: list[str]) -> list[dict]:
    """
    Convert criterion short codes into criterion data    dictionaries.

    Parameters
    ----------
    codes : list[str]
        List of criterion short codes (e.g., ``["KS", "AD"]``).

    Returns
    -------
    list[dict]
        List of dictionaries, each containing ``"criterion_code"`` and an
        empty ``"parameters"`` list.
    """
    criteria_data = []
    for code in codes:
        criterion = {"criterion_code": code, "parameters": []}
        criteria_data.append(criterion)

    return criteria_data
