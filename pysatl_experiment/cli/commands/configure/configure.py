from click import ClickException, Context, argument, pass_context

from pysatl_experiment.cli.cli import cli
from pysatl_experiment.cli.commands.common.common import read_experiment_data
from pysatl_experiment.validation.cli.commands.common.common import if_experiment_exists


@cli.group()
@argument("name")
@pass_context
def configure(ctx: Context, name: str) -> None:
    """
    Configure experiment parameters.

    :param ctx: context.
    :param name: name of the experiment.
    """

    experiment_exists = if_experiment_exists(name)
    if not experiment_exists:
        raise ClickException(f"Experiment with name {name} does not exist.")

    experiment_data = read_experiment_data(name)

    ctx.obj = {"experiment_data": experiment_data}
