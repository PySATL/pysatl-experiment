from enum import Enum
from typing import cast

from click import ClickException
from dacite import Config, from_dict

from stattest.cli.commands.common.common import create_result_path
from stattest.configuration.experiment_config.critical_value.critical_value import CriticalValueExperimentConfig
from stattest.configuration.experiment_config.experiment_config import ExperimentConfig
from stattest.configuration.experiment_config.power.power import PowerExperimentConfig
from stattest.configuration.experiment_config.time_complexity.time_complexity import TimeComplexityExperimentConfig
from stattest.configuration.experiment_data.common.steps_done.steps_done import StepsDone
from stattest.configuration.experiment_data.experiment_data import ExperimentData
from stattest.configuration.model.experiment_type.experiment_type import ExperimentType
from stattest.configuration.model.hypothesis.hypothesis import Hypothesis
from stattest.configuration.model.run_mode.run_mode import RunMode
from stattest.configuration.model.step_type.step_type import StepType
from stattest.persistence.experiment.sqlite.sqlite import SQLiteExperimentStorage
from stattest.persistence.model.experiment.experiment import ExperimentModel, ExperimentQuery, IExperimentStorage


def validate_build_and_run(experiment_data_dict: dict) -> ExperimentData:
    """
    Validate build and run command.

    :param experiment_data_dict: experiment data dictionary.
    """

    experiment_name = experiment_data_dict.get("experiment_name")
    if experiment_name is None:
        raise ClickException("Missing experiment_name")

    experiment_config = experiment_data_dict.get("config")
    if experiment_config is None:
        raise ClickException("Missing config")

    base_required_parameters = [
        "experiment_type",
        "storage_connection",
        "hypothesis",
        "sample_sizes",
        "monte_carlo_count",
    ]
    _check_required_parameters(experiment_config, base_required_parameters)

    experiment_type = experiment_config.get("experiment_type")
    if experiment_type == "power":
        power_required_parameters = ["significance_levels", "alternatives"]
        _check_required_parameters(experiment_config, power_required_parameters)
    elif experiment_type == "critical_value":
        critical_value_required_parameters = ["significance_levels"]
        _check_required_parameters(experiment_config, critical_value_required_parameters)

    experiment_config_dataclass = _create_experiment_config_from_dict(
        experiment_config_dict=experiment_config,
        experiment_type=experiment_type,
    )

    steps_done = StepsDone(
        is_generation_step_done=False,
        is_execution_step_done=False,
        is_report_building_step_done=False,
    )

    experiment_storage = SQLiteExperimentStorage(experiment_config_dataclass.storage_connection)
    experiment_storage.init()

    experiment_config_from_storage = _get_experiment_config_from_storage(
        config=experiment_config_dataclass,
        storage=experiment_storage,
    )
    if experiment_config_from_storage is not None:
        steps_done = _check_if_experiment_finished(experiment_config_from_storage)
    else:
        _save_experiment_config_to_storage(
            config=experiment_config_dataclass,
            storage=experiment_storage,
        )

    result_path = create_result_path(experiment_name)

    experiment_data = ExperimentData(
        name=experiment_name,
        config=experiment_config_dataclass,
        steps_done=steps_done,
        results_path=result_path,
    )

    return experiment_data


def _check_required_parameters(experiment_config: dict, required_parameters: list[str]) -> None:
    """
    Check if experiment configuration contains all required parameters.

    :param experiment_config: experiment configuration.
    :param required_parameters: required parameters.
    """

    missing_parameters = []

    for parameter in required_parameters:
        if parameter not in experiment_config:
            missing_parameters.append(parameter)

    is_need_to_configure = len(missing_parameters) > 0
    if is_need_to_configure:
        _raise_missing_parameters_exception(missing_parameters)


def _raise_missing_parameters_exception(missing_parameters: list[str]) -> None:
    """
    Raise exception with missing parameters.

    :param missing_parameters: missing parameters.
    """
    raise ClickException(f"Experiment configuration is missing required parameters: {missing_parameters}.")


def _create_experiment_config_from_dict(
    experiment_config_dict: dict,
    experiment_type: str,
) -> ExperimentConfig:
    """
    Create experiment data from dictionary.

    :param experiment_config_dict: experiment configuration dictionary.
    :param experiment_type: experiment type.

    :return: experiment config.
    """

    experiment_type_str_to_class = {
        "power": PowerExperimentConfig,
        "critical_value": CriticalValueExperimentConfig,
        "time_complexity": TimeComplexityExperimentConfig,
    }

    enum_mapping = {
        ExperimentType: lambda x: ExperimentType(x),
        RunMode: lambda x: RunMode(x),
        Hypothesis: lambda x: Hypothesis(x),
        StepType: lambda x: StepType(x),
    }

    experiment_config_type = experiment_type_str_to_class[experiment_type]

    experiment_config: ExperimentConfig = from_dict(
        data_class=experiment_config_type,
        data=experiment_config_dict,
        config=Config(type_hooks=enum_mapping, cast=[Enum]),
    )

    return experiment_config


def _get_experiment_config_from_storage(config: ExperimentConfig, storage: IExperimentStorage) -> ExperimentModel:
    """
    Get experiment config from database.

    :param config: experiment config dataclass.

    :return: experiment config from db.
    """

    experiment_type = config.experiment_type
    criteria = {criterion.criterion_code: criterion.parameters for criterion in config.criteria}

    significance_levels = []
    alternatives = {}
    if experiment_type == ExperimentType.CRITICAL_VALUE:
        critical_value_config = cast(PowerExperimentConfig, config)
        significance_levels = critical_value_config.significance_levels
    elif experiment_type == ExperimentType.POWER:
        power_config = cast(PowerExperimentConfig, config)
        significance_levels = power_config.significance_levels
        alternatives = {alternative.generator_name: alternative.parameters for alternative in power_config.alternatives}

    query = ExperimentQuery(
        experiment_type=experiment_type.value,
        storage_connection=config.storage_connection,
        run_mode=config.run_mode.value,
        hypothesis=config.hypothesis.value,
        generator_type=config.generator_type.value,
        executor_type=config.executor_type.value,
        report_builder_type=config.report_builder_type.value,
        sample_sizes=config.sample_sizes,
        monte_carlo_count=config.monte_carlo_count,
        criteria=criteria,
        significance_levels=significance_levels,
        alternatives=alternatives,
    )

    experiment_config_from_db = storage.get_data(query)

    return experiment_config_from_db


def _save_experiment_config_to_storage(config: ExperimentConfig, storage: IExperimentStorage) -> None:
    """
    Save experiment config to database.

    :param config: experiment config dataclass.
    :param storage: experiment storage.
    """

    experiment_type = config.experiment_type
    criteria = {criterion.criterion_code: criterion.parameters for criterion in config.criteria}

    significance_levels = []
    alternatives = {}
    if experiment_type == ExperimentType.CRITICAL_VALUE:
        critical_value_config = cast(PowerExperimentConfig, config)
        significance_levels = critical_value_config.significance_levels
    elif experiment_type == ExperimentType.POWER:
        power_config = cast(PowerExperimentConfig, config)
        significance_levels = power_config.significance_levels
        alternatives = {alternative.generator_name: alternative.parameters for alternative in power_config.alternatives}

    query = ExperimentModel(
        experiment_type=experiment_type.value,
        storage_connection=config.storage_connection,
        run_mode=config.run_mode.value,
        hypothesis=config.hypothesis.value,
        generator_type=config.generator_type.value,
        executor_type=config.executor_type.value,
        report_builder_type=config.report_builder_type.value,
        sample_sizes=config.sample_sizes,
        monte_carlo_count=config.monte_carlo_count,
        criteria=criteria,
        significance_levels=significance_levels,
        alternatives=alternatives,
        is_generation_done=False,
        is_execution_done=False,
        is_report_building_done=False,
    )

    storage.insert_data(query)


def _check_if_experiment_finished(experiment_config_from_db: ExperimentModel) -> StepsDone:
    """
    Check if experiment is finished.

    :param experiment_config_from_db: experiment config from db.
    """

    is_generation_done = experiment_config_from_db.is_generation_done
    is_execution_done = experiment_config_from_db.is_execution_done
    is_report_building_done = experiment_config_from_db.is_report_building_done

    if is_generation_done and is_execution_done and is_report_building_done:
        raise ClickException("Experiment is already finished.")

    steps_done = StepsDone(
        is_generation_step_done=is_generation_done,
        is_execution_step_done=is_execution_done,
        is_report_building_step_done=is_report_building_done,
    )

    return steps_done
