from click import BadParameter, argument, command

from stattest.cli.commands.common.common import get_experiment_config, read_experiment_data
from stattest.configuration.experiment_config.experiment_config import ExperimentConfig
from stattest.configuration.experiment_data.experiment_data import ExperimentData
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

    experiment_data = validate_build_and_run(experiment_data_dict)

    experiment_type = experiment_config["experiment_type"]

    experiment_steps = _build_experiment(experiment_data, experiment_type)

    experiment = Experiment(experiment_steps)

    experiment.run_experiment()


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
