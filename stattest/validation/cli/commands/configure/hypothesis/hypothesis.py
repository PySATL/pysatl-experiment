from click import BadParameter

from stattest.cli.commands.common.common import list_possible_parameter_values
from stattest.configuration.model.hypothesis.hypothesis import Hypothesis


def validate_hypothesis(hypothesis: str) -> None:
    """
    Check if hypothesis is valid.

    :param hypothesis: hypothesis.
    """
    hypothesis_lower = hypothesis.lower()
    if hypothesis_lower not in (item.value for item in Hypothesis):
        possible_values = list_possible_parameter_values(Hypothesis)
        raise BadParameter(f"Hypothesis '{hypothesis}' is not valid.\nPossible values are: {possible_values}.")
