"""CLI command for building and executing experiments."""

from typing import Any, cast

from click import BadParameter, Choice, FloatRange, argument, command, option
from click_loglevel import LogLevel

from pysatl_experiment.cli.validation.commands.build_and_run import validate_build_and_run
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.task_failure_policy import TaskFailurePolicy
from pysatl_experiment.experiment_execution.experiment import Experiment
from pysatl_experiment.experiment_execution.experiment_factory import (
    CriticalValueExperimentFactory,
    GenerationOnlyExperimentFactory,
    PowerExperimentFactory,
    TimeComplexityExperimentFactory,
)
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.loggers import setup_logging
from pysatl_experiment.utils.experiment_utils import is_experiment_exists, read_experiment_data


# TODO: refactor names!


@command()
@argument("name")
@option("-l", "--log-level", type=LogLevel(), default="WARNING", help="Set logging level", show_default=True)
@option("--log-file", help="Set logging file")
@option(
    "--task-failure-policy",
    type=Choice(TaskFailurePolicy.list()),
    default=None,
    help="Override the task failure policy from the experiment configuration.",
)
@option(
    "--failure-threshold",
    type=FloatRange(0.0, 1.0),
    default=None,
    help="Override the allowed share of failed tasks under the isolate policy.",
)
def build_and_run(
    name: str,
    log_level: int,
    log_file: str,
    task_failure_policy: str | None,
    failure_threshold: float | None,
) -> None:
    """
    Build and execute an experiment.

    Parameters
    ----------
    name : str
        Experiment name. The ``.json`` extension is optional.
    log_level : int
        Logging level.
    log_file : str
        Logging file name.
    task_failure_policy : str | None
        Task failure policy overriding the configured one.
    failure_threshold : float | None
        Allowed share of failed tasks overriding the configured one.

    Raises
    ------
    click.BadParameter
        If the experiment does not exist.
    """
    if not is_experiment_exists(name):
        raise BadParameter(f"Experiment with name {name} does not exist.")

    experiment_configuration = read_experiment_data(name)

    setup_logging(experiment_configuration, log_level, log_file)

    experiment_data = validate_build_and_run(experiment_configuration)
    _apply_failure_policy_overrides(experiment_data, task_failure_policy, failure_threshold)
    _run_experiment_data(experiment_data)


def _apply_failure_policy_overrides(
    experiment_data: ExperimentData[Any],
    task_failure_policy: str | None,
    failure_threshold: float | None,
) -> None:
    """
    Apply CLI failure-policy overrides to the validated configuration.

    CLI flags take precedence over the experiment configuration file.
    Generation-only experiments do not run criteria tasks, so the
    overrides are silently ignored for them.

    Parameters
    ----------
    experiment_data : ExperimentData
        Validated experiment data.
    task_failure_policy : str | None
        Task failure policy value from the CLI, if provided.
    failure_threshold : float | None
        Failure threshold value from the CLI, if provided.
    """
    config = experiment_data.config
    if not hasattr(config, "task_failure_policy"):
        return

    if task_failure_policy is not None:
        config.task_failure_policy = TaskFailurePolicy(task_failure_policy)
    if failure_threshold is not None:
        config.failure_threshold = failure_threshold


def _run_experiment_data(experiment_data: ExperimentData[Any]) -> None:
    """Build and execute the validated experiment pipeline."""
    experiment_steps = _build_experiment(experiment_data)
    Experiment(experiment_steps).run_experiment()


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
        ExperimentType.GENERATION_ONLY: GenerationOnlyExperimentFactory,
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
