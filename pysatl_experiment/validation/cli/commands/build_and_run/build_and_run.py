from enum import Enum
from typing import cast

from click import ClickException
from dacite import Config, from_dict
from pydantic import ValidationError

from pysatl_experiment.cli.commands.common.common import create_result_path
from pysatl_experiment.configuration.experiment_config.critical_value.critical_value import (
    CriticalValueExperimentConfig as LegacyCriticalValueExperimentConfig,
)
from pysatl_experiment.configuration.experiment_config.experiment_config import ExperimentConfig
from pysatl_experiment.configuration.experiment_config.power.power import (
    PowerExperimentConfig as LegacyPowerExperimentConfig,
)
from pysatl_experiment.configuration.experiment_config.time_complexity.time_complexity import (
    TimeComplexityExperimentConfig as LegacyTimeComplexityExperimentConfig,
)
from pysatl_experiment.configuration.experiment_data.common.steps_done.steps_done import StepsDone
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.persistence.experiment.sqlite.sqlite import SQLiteExperimentStorage
from pysatl_experiment.persistence.model.experiment.experiment import (
    ExperimentModel,
    ExperimentQuery,
    IExperimentStorage,
)
from pysatl_experiment.validation.cli.commands.common.checker import SQLiteCriticalValueChecker
from pysatl_experiment.validation.cli.schemas.experiment import BaseExperimentConfig as PydanticBaseExperiment
from pysatl_experiment.validation.cli.schemas.experiment import CriticalValueConfig as PydanticCriticalValueConfig
from pysatl_experiment.validation.cli.schemas.experiment import ExperimentConfig as ExperimentInputSchema
from pysatl_experiment.validation.cli.schemas.experiment import PowerConfig as PydanticPowerConfig
from pysatl_experiment.validation.cli.schemas.experiment import TimeComplexityConfig as PydanticTimeComplexityConfig


def validate_build_and_run(experiment_data_dict: dict) -> ExperimentData:
    """
    Validates input, initializes, and builds the experiment data object.

    This function performs the following steps:
    1.  Conditionally creates a database checker if the experiment is a 'power'
        analysis.
    2.  Validates the raw input dictionary against Pydantic schemas, passing the
        database checker in the context to allow for stateful validation (e.g.,
        ensuring required critical values exist).
    3.  Adapts the validated Pydantic models to legacy dataclass configurations.
    4.  Initializes the SQLite storage backend.
    5.  Checks if an identical experiment already exists in storage to resume it.
    6.  If not, it saves the new experiment configuration to the database.
    7.  Creates a results path for experiment artifacts.
    8.  Returns a complete `ExperimentData` object to be used by the runner.

    Args:
        experiment_data_dict: A dictionary containing the raw experiment configuration.

    Raises:
        ClickException: If validation fails (with detailed, user-friendly error
            messages for each invalid field) or if the experiment has already
            been completed.

    Returns:
        An `ExperimentData` object ready for the experiment execution pipeline.
    """
    try:
        checker = None
        config_dict = experiment_data_dict.get("config", {})

        if config_dict.get("experiment_type") == "power":
            connection_str = config_dict.get("storage_connection")
            if not connection_str:
                pass
            else:
                checker = SQLiteCriticalValueChecker(connection_string=connection_str)

        validation_context = {"critical_value_checker": checker} if checker else {}

        validated_data = ExperimentInputSchema.model_validate(experiment_data_dict, context=validation_context)

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            if error["type"] == "value_error":
                error_messages.append(error["msg"])
            elif error["type"] == "missing":
                field_path = ".".join(map(str, error["loc"]))
                error_messages.append(f"A required parameter is missing: '{field_path}'")
            else:
                field_path = ".".join(map(str, error["loc"]))
                error_messages.append(f"Error in the field '{field_path}': {error['msg']}")

        final_error_message = "\n".join(error_messages)
        raise ClickException(final_error_message)

    experiment_name = validated_data.name
    pydantic_config = validated_data.config

    legacy_dataclass_config = _adapt_pydantic_to_dataclass(pydantic_config)
    steps_done = StepsDone(
        is_generation_step_done=False,
        is_execution_step_done=False,
        is_report_building_step_done=False,
    )

    experiment_storage = SQLiteExperimentStorage(legacy_dataclass_config.storage_connection)
    experiment_storage.init()

    experiment_config_from_storage = _get_experiment_config_from_storage(
        config=legacy_dataclass_config,
        storage=experiment_storage,
    )
    if experiment_config_from_storage is not None:
        steps_done = _check_if_experiment_finished(experiment_config_from_storage)
    else:
        _save_experiment_config_to_storage(
            config=legacy_dataclass_config,
            storage=experiment_storage,
        )

    result_path = create_result_path()

    experiment_data = ExperimentData(
        name=experiment_name,
        config=legacy_dataclass_config,
        steps_done=steps_done,
        results_path=result_path,
    )

    return experiment_data


def _get_experiment_config_from_storage(
    config: ExperimentConfig, storage: IExperimentStorage
) -> ExperimentModel | None:
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
        critical_value_config = cast(LegacyCriticalValueExperimentConfig, config)
        significance_levels = critical_value_config.significance_levels
    elif experiment_type == ExperimentType.POWER:
        power_config = cast(LegacyPowerExperimentConfig, config)
        significance_levels = power_config.significance_levels
        alternatives = {alternative.generator_name: alternative.parameters for alternative in power_config.alternatives}

    query = ExperimentQuery(
        experiment_type=experiment_type.value,
        storage_connection=config.storage_connection,
        run_mode=config.run_mode.value,
        report_mode=config.report_mode.value,
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
        critical_value_config = cast(LegacyCriticalValueExperimentConfig, config)
        significance_levels = critical_value_config.significance_levels
    elif experiment_type == ExperimentType.POWER:
        power_config = cast(LegacyPowerExperimentConfig, config)
        significance_levels = power_config.significance_levels
        alternatives = {alternative.generator_name: alternative.parameters for alternative in power_config.alternatives}

    query = ExperimentModel(
        experiment_type=experiment_type.value,
        storage_connection=config.storage_connection,
        run_mode=config.run_mode.value,
        report_mode=config.report_mode.value,
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


# Maps modern Pydantic config classes to their legacy dataclass counterparts.
PYDANTIC_TO_LEGACY_MAP = {
    PydanticPowerConfig: LegacyPowerExperimentConfig,
    PydanticCriticalValueConfig: LegacyCriticalValueExperimentConfig,
    PydanticTimeComplexityConfig: LegacyTimeComplexityExperimentConfig,
}


def _adapt_pydantic_to_dataclass(pydantic_config: PydanticBaseExperiment) -> ExperimentConfig:
    """
    Converts a Pydantic configuration model to a legacy dataclass model.

    This adapter function is necessary for compatibility between the new
    Pydantic-based validation layer and the older, dataclass-based core
    logic. It uses `dacite` for flexible conversion.

    Args:
        pydantic_config: The validated Pydantic configuration object.

    Raises:
        TypeError: If the Pydantic config type has no corresponding legacy class
            in the `PYDANTIC_TO_LEGACY_MAP`.

    Returns:
        The equivalent legacy `ExperimentConfig` dataclass instance.
    """
    legacy_dataclass_type = PYDANTIC_TO_LEGACY_MAP.get(type(pydantic_config))
    if legacy_dataclass_type is None:
        raise TypeError(f"No match for Pydantic type: {type(pydantic_config)}")

    config_dict = pydantic_config.model_dump(mode="json")

    enum_mapping = {
        ExperimentType: lambda x: ExperimentType(x),
        RunMode: lambda x: RunMode(x),
        Hypothesis: lambda x: Hypothesis(x),
        StepType: lambda x: StepType(x),
    }

    legacy_config = from_dict(
        data_class=legacy_dataclass_type,
        data=config_dict,
        config=Config(type_hooks=enum_mapping, cast=[Enum]),
    )

    return legacy_config
