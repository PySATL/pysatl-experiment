from enum import Enum

from click import BadParameter, argument, command
from dacite import Config, from_dict

from stattest.cli.commands.common.common import get_experiment_config, read_experiment_data
from stattest.configuration.experiment_config.experiment_config import ExperimentConfig
from stattest.configuration.experiment_data.critical_value.critical_value import (
    CriticalValueExperimentData,
)
from stattest.configuration.experiment_data.experiment_data import ExperimentData
from stattest.configuration.experiment_data.power.power import PowerExperimentData
from stattest.configuration.experiment_data.time_complexity.time_complexity import (
    TimeComplexityExperimentData,
)
from stattest.configuration.model.experiment_type.experiment_type import ExperimentType
from stattest.configuration.model.hypothesis.hypothesis import Hypothesis
from stattest.configuration.model.run_mode.run_mode import RunMode
from stattest.configuration.model.step_type.step_type import StepType
from stattest.experiment_new.experiment.experiment import Experiment
from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.factory.critical_value.critical_value import CriticalValueExperimentFactory
from stattest.factory.power.power import PowerExperimentFactory
from stattest.factory.time_complexity.time_complexity import TimeComplexityExperimentFactory
from stattest.validation.cli.commands.build_and_run.build_and_run import validate_build_and_run
from stattest.validation.cli.commands.common.common import if_experiment_exists


@command()
@argument("name")
def build_and_run(name: str) -> None:
    """
    Build and run an experiment with the given name.

    :param name: name of the experiment.
    """

    experiment_exists = if_experiment_exists(name)
    if not experiment_exists:
        raise BadParameter(f"Experiment with name {name} does not exists.")

    experiment_data_dict = read_experiment_data(name)
    experiment_config = get_experiment_config(experiment_data_dict)

    validate_build_and_run(experiment_config)

    experiment_type = experiment_config["experiment_type"]

    experiment_data = _create_experiment_data_from_dict(experiment_data_dict, experiment_type)

    experiment_steps = _build_experiment(experiment_data, experiment_type)

    experiment = Experiment(experiment_steps)

    experiment.run_experiment()


def _create_experiment_data_from_dict(
    experiment_data_dict: dict,
    experiment_type: str,
) -> ExperimentData[ExperimentConfig]:
    """
    Create experiment data from dictionary.

    :param experiment_data_dict: experiment data dictionary.
    :param experiment_type: experiment type.

    :return: experiment data.
    """

    experiment_type_str_to_class = {
        "power": PowerExperimentData,
        "critical_value": CriticalValueExperimentData,
        "time_complexity": TimeComplexityExperimentData,
    }

    enum_mapping = {
        "experiment_type": ExperimentType,
        "run_mode": RunMode,
        "hypothesis": Hypothesis,
        "data_generator_type": StepType,
        "executor_type": StepType,
        "report_builder_type": StepType,
    }

    experiment_data_type = experiment_type_str_to_class[experiment_type]

    experiment_data = from_dict(
        data_class=experiment_data_type,
        data=experiment_data_dict,
        config=Config(type_hooks=enum_mapping, cast=[Enum]),
    )

    return experiment_data


def _build_experiment(
    experiment_data: ExperimentData[ExperimentConfig], experiment_type: str
) -> ExperimentSteps:
    """
    Build experiment.

    :param experiment_data: experiment data.
    :param experiment_type: experiment type.

    :return: experiment steps.
    """

    experiment_type_to_factory = {
        "power": PowerExperimentFactory,
        "critical_value": CriticalValueExperimentFactory,
        "time_complexity": TimeComplexityExperimentFactory,
    }

    experiment_factory = experiment_type_to_factory[experiment_type]

    experiment_steps = experiment_factory(experiment_data).create_experiment_steps()

    return experiment_steps
