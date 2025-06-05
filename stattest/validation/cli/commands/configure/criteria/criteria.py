from click import BadParameter

from stattest.cli.commands.common.common import get_statistics_codes_for_hypothesis


def validate_criteria(criteria_codes: list[str], hypothesis: str) -> None:
    """
    Validate experiment criteria.

    :param criteria_codes: criteria codes.
    :param hypothesis: hypothesis.
    """

    valid_criteria_codes = get_statistics_codes_for_hypothesis(hypothesis)

    for code in criteria_codes:
        if code not in valid_criteria_codes:
            raise BadParameter(
                f"Criterion '{code}' is not allowed for hypothesis '{hypothesis}'.\n"
                f"Possible values are: {', '.join(valid_criteria_codes)}"
            )
