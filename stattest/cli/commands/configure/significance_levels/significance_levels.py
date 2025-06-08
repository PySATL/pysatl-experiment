from click import ClickException, Context, FloatRange, argument, echo, pass_context

from stattest.cli.commands.common.common import (
    get_experiment_name_and_config,
    save_experiment_config,
)
from stattest.cli.commands.configure.configure import configure


@configure.command()
@argument("levels", nargs=-1, type=FloatRange(min=0.0, max=1.0, min_open=True, max_open=True))
@pass_context
def significance_levels(ctx: Context, levels: tuple[float, ...]) -> None:
    """
    Configure experiment significance levels.

    :param ctx: context.
    :param levels: significance levels (0<sl<1).
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_type = experiment_config.get("experiment_type")
    if experiment_type is None:
        raise ClickException(
            f"Experiment type is not configured.\n"
            f"Please, configure it first by calling "
            f"'experiment configure {experiment_name} experiment_type <type>'."
        )
    elif experiment_type == "time_complexity":
        raise ClickException(
            "Significance levels are not supported for time complexity experiments."
        )

    levels_list = list(levels)
    experiment_config["significance_levels"] = levels_list

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Significance levels of the experiment '{experiment_name}' are set to {levels_list}.")
