"""CLI command for building and executing experiments."""

from typing import Any, cast

from click import BadParameter, argument, command, option
from click_loglevel import LogLevel

from pysatl_experiment.cli.commands.common.common import normalize_experiment_name, read_experiment_data
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.experiment.experiment.experiment import Experiment
from pysatl_experiment.experiment.experiment_steps.experiment_steps import ExperimentSteps
from pysatl_experiment.factory.critical_value.critical_value import CriticalValueExperimentFactory
from pysatl_experiment.factory.power.power import PowerExperimentFactory
from pysatl_experiment.factory.time_complexity.time_complexity import TimeComplexityExperimentFactory
from pysatl_experiment.loggers import setup_logging
from pysatl_experiment.validation.cli.commands.build_and_run.build_and_run import validate_build_and_run
from pysatl_experiment.validation.cli.commands.common.common import if_experiment_exists


# TODO: refactor names!


@command()
@argument("name")
@option("-l", "--log-level", type=LogLevel(), default="WARNING", help="Set logging level", show_default=True)
@option("--log-file", help="Set logging file")
def build_and_run(name: str, log_level: int, log_file: str) -> None:
    """
    Build and execute an experiment.

    Parameters
    ----------
    name : str
        Experiment name. The ``.json`` extension is optional.

    Raises
    ------
    click.BadParameter
        If the experiment does not exist.
        @param log_file: log file name
        @param name: experiment name
        @param log_level: log level
    """
    name = normalize_experiment_name(name)

    if not if_experiment_exists(name):
        raise BadParameter(f"Experiment with name {name} does not exist.")

    experiment_configuration = read_experiment_data(name)

    setup_logging(experiment_configuration, log_level, log_file)

    experiment_data = validate_build_and_run(experiment_configuration)
    experiment_steps = _build_experiment(experiment_data)

    experiment = Experiment(experiment_steps)
    experiment.run_experiment()


def _build_experiment(experiment_data: ExperimentData) -> ExperimentSteps:
    """
    Create experiment steps from validated configuration.

    Parameters
    ----------
    experiment_data : ExperimentData
        Validated experiment configuration.

    Returns
    -------
    ExperimentSteps
        Experiment steps ready for execution.
    """
    experiment_type_to_factory = {
        ExperimentType.POWER: PowerExperimentFactory,
        ExperimentType.CRITICAL_VALUE: CriticalValueExperimentFactory,
        ExperimentType.TIME_COMPLEXITY: TimeComplexityExperimentFactory,
    }

    experiment_type = experiment_data.config.experiment_type

    experiment_factory = experiment_type_to_factory.get(experiment_type)

    if experiment_factory is None:
        raise BadParameter(f"Unsupported experiment type: {experiment_type}.")

    validated_experiment_data = cast(
        Any,
        experiment_data,
    )
    return experiment_factory(
        validated_experiment_data,
    ).create_experiment_steps()
