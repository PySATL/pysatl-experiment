from click import argument, command, echo, option, Choice

from pysatl_experiment.cli.commands.common.common import get_statistics_short_codes_for_hypothesis
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


@command()
@argument("distribution", type=Choice(Hypothesis.list()),)
@option('--description/--no-description', '-y/-n', default=False, help="Show criteria description")
def available_criteria(distribution: str, description: bool) -> None:
    """
    Collect all existing criteria.

    :param distribution: distribution.
    """

    codes = get_statistics_short_codes_for_hypothesis(distribution)

    echo(f"Available criteria for {distribution}:")
    if len(codes) > 0:
        for code in codes:
            echo(f"code: {code}")
    else:
        echo("No criteria found")
