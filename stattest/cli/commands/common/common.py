import json
from enum import Enum
from pathlib import Path

from click import ClickException, Context
from pysatl_criterion.statistics import (
    AbstractExponentialityGofStatistic,
    AbstractNormalityGofStatistic,
    AbstractWeibullGofStatistic,
)


def create_experiment_path(name: str) -> Path:
    """
    Create experiment path.

    :param name: name of the experiment.

    :return: path to the experiment.
    """

    # pysatl-experiment/.experiments
    experiments_dir = Path(__file__).resolve().parents[4] / ".experiments"
    experiment_file_name = f"{name}.json"

    experiment_path = experiments_dir / experiment_file_name

    return experiment_path


def save_experiment_data(experiment_name: str, experiment_data: dict) -> None:
    """
    Save experiment data.

    :param experiment_name: path to the experiment.
    :param experiment_data: experiment data.
    """

    experiment_path = create_experiment_path(experiment_name)
    with Path.open(experiment_path, "w") as f:
        json.dump(experiment_data, f)


def read_experiment_data(experiment_name: str) -> dict:
    """
    Read experiment data.

    :param experiment_name: path to the experiment.

    :return: experiment data.
    """

    experiment_path = create_experiment_path(experiment_name)
    with Path.open(experiment_path) as f:
        data = json.load(f)

    return dict(data)


def list_possible_parameter_values(param_type: type[Enum]) -> str:
    """
    List possible parameter values.

    :param param_type: parameter type.

    :return: possible parameter values.
    """

    param_type_values = [item.value for item in param_type]
    param_type_values_str = ", ".join(param_type_values)

    return param_type_values_str


def get_statistics_codes_for_hypothesis(hypothesis: str) -> list[str]:
    """
    Get statistics codes for hypothesis.

    :param hypothesis: hypothesis.

    :return: statistics codes for hypothesis.
    """

    hypothesis_to_base_class = {
        "exponential": AbstractExponentialityGofStatistic,
        "normal": AbstractNormalityGofStatistic,
        "weibull": AbstractWeibullGofStatistic,
    }

    base_class = hypothesis_to_base_class[hypothesis]

    valid_criteria_types = [cls for cls in base_class.__subclasses__()]
    valid_criteria_codes = [cls.code().split("_")[0] for cls in valid_criteria_types]

    return valid_criteria_codes


def get_experiment_data(ctx: Context) -> dict:
    """
    Get experiment data.

    :param ctx: context.

    :return: experiment data.
    """

    experiment_data = ctx.obj.get("experiment_data")
    if experiment_data is None:
        raise ClickException("Experiment is not created.")

    return experiment_data


def get_experiment_name(experiment_data: dict) -> str:
    """
    Get experiment name.

    :param experiment_data: experiment data.

    :return: experiment name.
    """

    experiment_name = experiment_data.get("name")
    if experiment_name is None:
        raise ClickException("Experiment name is not configured.")

    return experiment_name


def get_experiment_config(experiment_data: dict) -> dict:
    """
    Get experiment config.

    :param experiment_data: experiment data.

    :return: experiment config.
    """

    experiment_config = experiment_data.get("config")
    if experiment_config is None:
        raise ClickException("Experiment config is not configured.")

    return experiment_config


def get_experiment_name_and_config(ctx: Context) -> tuple[str, dict]:
    """
    Get experiment name and config from context.

    :param ctx: context.

    :return: experiment name and config.
    """

    experiment_data = get_experiment_data(ctx)
    experiment_name = get_experiment_name(experiment_data)
    experiment_config = get_experiment_config(experiment_data)

    return experiment_name, experiment_config


def save_experiment_config(ctx: Context, experiment_name: str, experiment_config: dict) -> None:
    """
    Save experiment config.

    :param ctx: context.
    :param experiment_name: experiment name.
    :param experiment_config: experiment config.

    :return: experiment config.
    """

    experiment_data = get_experiment_data(ctx)
    experiment_data["config"] = experiment_config
    save_experiment_data(experiment_name, experiment_data)
