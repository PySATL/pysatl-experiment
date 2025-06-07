from click import Context, IntRange, argument, echo, pass_context

from stattest.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from stattest.cli.commands.configure.configure import configure


@configure.command()
@argument("count", type=IntRange(min=100))
@pass_context
def monte_carlo_count(ctx: Context, count: int) -> None:
    """
    Configure experiment Monte Carlo number of iterations.

    :param ctx: context.
    :param count: monte carlo number of iterations (min=100).
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_config["monte_carlo_count"] = count

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Monte Carlo number of iterations of the experiment '{experiment_name}' is set to {count}.")
