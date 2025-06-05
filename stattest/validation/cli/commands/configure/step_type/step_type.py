from click import BadParameter

from stattest.cli.commands.common.common import list_possible_parameter_values
from stattest.configuration.model.step_type.step_type import StepType


def validate_step_type(step_type: str, step: str) -> None:
    """
    Check if step type is valid.

    :param step_type: step type.
    :param step: step.
    """

    step_type_lower = step_type.lower()
    if step_type_lower not in (item.value for item in StepType):
        possible_values = list_possible_parameter_values(StepType)
        raise BadParameter(
            f"Type of {step} '{step_type}' is not valid.\n"
            f"Possible values are: {possible_values}."
        )

    if step_type_lower == "custom":
        raise BadParameter(
            f"Custom {step} type is not supported yet.\n" f"Please, choose standard one."
        )
