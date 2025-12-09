from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.step_type.step_type import StepType


@configure.command()
@argument("report_build_type")
@pass_context
def report_builder_type(ctx: Context, report_build_type: str) -> None:
    """
    Set the report builder type for the current experiment.

    This command configures which report builder will be used to generate the
    final output and artifacts of the experiment. The type must be one of the
    predefined values in `StepType`.

    Example:
        experiment configure MyReportTest report-builder-type standard

    Args:
        ctx: The Click context object, passed automatically.
        report_build_type: The desired report builder type (e.g., 'standard').
            The value is case-insensitive.
    """

    try:
        validated_step = StepType(report_build_type.lower())
    except ValueError:
        valid_options = [e.value for e in StepType]
        raise BadParameter(f"Type of '{report_build_type}' is not valid.\nPossible values are: {valid_options}.")

    if validated_step == StepType.CUSTOM:
        raise BadParameter("Custom type is not supported yet.\nPlease, choose standard one")

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    report_build_type_lower = report_build_type.lower()
    experiment_config["report_builder_type"] = report_build_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Report builder type of the experiment '{experiment_name}' is set to '{report_build_type_lower}'.")
