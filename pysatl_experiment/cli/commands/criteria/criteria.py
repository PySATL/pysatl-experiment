"""CLI command for configuring experiments."""

from click import Choice, argument, command, echo, option

from pysatl_experiment.cli.commands.common.common import get_statistics_short_codes_for_hypothesis
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


@command()
@argument(
    "distribution",
    type=Choice(Hypothesis.list()),
)
@option(
    "--description/--no-description",
    "-y/-n",
    default=False,
    help="Show criteria description.",
)
def available_criteria(distribution: str, description: bool) -> None:
    """
    Show available criteria for a distribution.

    Parameters
    ----------
    distribution : str
        Distribution hypothesis name.
    description : bool
        Whether to display criterion descriptions.

    Notes
    -----
    Currently, the ``description`` option is reserved for future use.
    """
    codes = get_statistics_short_codes_for_hypothesis(distribution)  # TODO: name!!

    # TODO: description support!

    echo(f"Available criteria for {distribution}:")
    if len(codes) > 0:
        for code in codes:
            echo(f"code: {code}")
    else:
        echo("No criteria found")
