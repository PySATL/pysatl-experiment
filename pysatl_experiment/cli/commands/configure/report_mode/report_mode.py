from click import Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.validation.cli.commands.configure.report_mode.report_mode import validate_report_mode


@configure.command()
@argument("mode")
@pass_context
def report_mode(ctx: Context, mode: str) -> None:
    """
    Configure experiment report mode.

    :param ctx: context.
    :param mode: report mode.
    """

    validate_report_mode(mode)
    mode_lower = mode.lower()

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_config["report_mode"] = mode_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Report mode of the experiment '{experiment_name}' is set to '{mode_lower}'.")
