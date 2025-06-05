from click import BadParameter

from stattest.cli.commands.common.common import list_possible_parameter_values
from stattest.configuration.model.run_mode.run_mode import RunMode


def validate_run_mode(run_mode: str) -> None:
    """
    Check if run mode is valid.

    :param run_mode: run mode.
    """
    run_mode_lower = run_mode.lower()
    if run_mode_lower not in (item.value for item in RunMode):
        possible_values = list_possible_parameter_values(RunMode)
        raise BadParameter(
            f"Run mode '{run_mode}' is not valid.\n" f"Possible values are: {possible_values}."
        )
