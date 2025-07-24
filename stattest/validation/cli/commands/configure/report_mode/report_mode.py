from click import BadParameter

from stattest.cli.commands.common.common import list_possible_parameter_values
from stattest.configuration.model.report_mode.report_mode import ReportMode


def validate_report_mode(report_mode: str) -> None:
    """
    Check if report mode is valid.

    :param report_mode: report mode string.
    """
    report_mode_lower = report_mode.lower()
    if report_mode_lower not in (item.value for item in ReportMode):
        possible_values = list_possible_parameter_values(ReportMode)
        raise BadParameter(
            f"Run mode '{report_mode}' is not valid.\nPossible values are: {possible_values}."
        )