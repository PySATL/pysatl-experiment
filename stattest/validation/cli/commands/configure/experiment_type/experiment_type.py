from click import BadParameter

from stattest.cli.commands.common.common import list_possible_parameter_values
from stattest.configuration.model.experiment_type.experiment_type import ExperimentType


def validate_experiment_type(experiment_type: str) -> None:
    """
    Check if experiment type is valid.

    :param experiment_type: experiment type.
    """

    experiment_type_lower = experiment_type.lower()
    if experiment_type_lower not in (item.value for item in ExperimentType):
        possible_values = list_possible_parameter_values(ExperimentType)
        raise BadParameter(
            f"Experiment type '{experiment_type}' is not valid.\n"
            f"Possible values are: {possible_values}."
        )
