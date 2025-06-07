from click import Context, IntRange, argument, echo, pass_context

from stattest.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from stattest.cli.commands.configure.configure import configure


@configure.command()
@argument("sizes", nargs=-1, type=IntRange(min=10))
@pass_context
def sample_sizes(ctx: Context, sizes: tuple[int, ...]) -> None:
    """
    Configure experiment sample sizes.

    :param ctx: context.
    :param sizes: sample sizes (min=10).
    """

    sizes_list = list(sizes)

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_config["sample_sizes"] = sizes_list

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Sample sizes of the experiment '{experiment_name}' are set to {sizes_list}.")
