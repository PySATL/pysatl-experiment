from click import BadParameter, argument, command

from pysatl_experiment.cli.commands.common.common import read_experiment_data
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.experiment_new.experiment.experiment import Experiment
from pysatl_experiment.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from pysatl_experiment.factory.critical_value.critical_value import CriticalValueExperimentFactory
from pysatl_experiment.factory.power.power import PowerExperimentFactory
from pysatl_experiment.factory.time_complexity.time_complexity import TimeComplexityExperimentFactory
from pysatl_experiment.validation.cli.commands.build_and_run.build_and_run_new import validate_build_and_run
from pysatl_experiment.validation.cli.commands.common.common import if_experiment_exists


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
    experiment_data = validate_build_and_run(experiment_data_dict)
    experiment_steps = _build_experiment(experiment_data)

    experiment = Experiment(experiment_steps)
    experiment.run_experiment()


def _build_experiment(experiment_data: ExperimentData) -> ExperimentSteps:
    """
    Build experiment from validated ExperimentData object.

    :param experiment_data: validated experiment data.
    :return: experiment steps.
    """
    experiment_type_to_factory = {
        "power": PowerExperimentFactory,
        "critical_value": CriticalValueExperimentFactory,
        "time_complexity": TimeComplexityExperimentFactory,
    }

    experiment_type_str = experiment_data.config.experiment_type.value

    experiment_factory = experiment_type_to_factory[experiment_type_str]

    experiment_steps = experiment_factory(experiment_data).create_experiment_steps()

    return experiment_steps
