from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode


@configure.command()
@argument("mode")
@pass_context
def report_mode(ctx: Context, mode: str) -> None:
    """Set the report generation mode for the current experiment.

    This command configures the style of the final report.
    The mode must be one of the predefined values in `ReportMode`.

    Example:
        experiment configure MyAnalysis report-mode with-chart

    Args:
        ctx: The Click context object, passed automatically.
        mode: The desired report mode (e.g., 'standard'). The value is
            case-insensitive.
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    try:
        validated_report_mode = ReportMode(mode.lower())
    except ValueError:
        valid_options = [e.value for e in ReportMode]
        raise BadParameter(f"Type of '{mode}' is not valid.\nPossible values are: {valid_options}.")

    experiment_config["report_mode"] = validated_report_mode.value

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Report mode of the experiment '{experiment_name}' is set to '{validated_report_mode.value}'.")
