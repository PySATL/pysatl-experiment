from click import Choice, command, echo, option
from pysatl_criterion.util.distribution import DistributionType

from pysatl_experiment.cli.commands.common.common import get_statistics_short_codes_for_hypothesis


def __show_available_criteria(distribution: str, codes: list[str]):
    echo(f"Available criteria for {distribution}:")
    if len(codes) > 0:
        for code in codes:
            echo(f"code: {code}")
    else:
        echo("No criteria found")


@command()
@option(
    "--distribution", "-d", required=False, type=Choice(DistributionType.list()), help="Distribution. Empty for all"
)
@option("--description/--no-description", "-y/-n", default=False, help="Show criteria description")
def available_criteria(distribution: str | None, description: bool) -> None:
    """
    Collect all existing criteria.

    :param distribution: distribution.
    """

    codes: list[str] | dict[str, list[str]] = get_statistics_short_codes_for_hypothesis(distribution)

    if distribution is None and isinstance(codes, dict):
        for key, value in codes.items():
            __show_available_criteria(key, value)
        return

    echo(f"Available criteria for {distribution}:")
    if len(codes) > 0:
        for code in codes:
            echo(f"code: {code}")
    else:
        echo("No criteria found")
