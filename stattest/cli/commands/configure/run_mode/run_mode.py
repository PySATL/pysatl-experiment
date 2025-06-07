from click import Context, argument, echo, pass_context

from stattest.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from stattest.cli.commands.configure.configure import configure
from stattest.validation.cli.commands.configure.run_mode.run_mode import validate_run_mode


@configure.command()
@argument("mode")
@pass_context
def run_mode(ctx: Context, mode: str) -> None:
    """
    Configure experiment run mode.

    :param ctx: context.
    :param mode: run mode.
    """

    validate_run_mode(mode)
    mode_lower = mode.lower()

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_config["run_mode"] = mode_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Run mode of the experiment '{experiment_name}' is set to '{mode_lower}'.")
