import json

from click import Context, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_data
from pysatl_experiment.cli.commands.configure.configure import configure


@configure.command()
@pass_context
def show(ctx: Context) -> None:
    """
    Show experiment data.

    :param ctx: context.
    """
    experiment_data = get_experiment_data(ctx)
    echo(json.dumps(experiment_data, indent=4))
