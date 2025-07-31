from click import Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.validation.cli.commands.configure.step_type.step_type import validate_step_type


@configure.command()
@argument("report_build_type")
@pass_context
def report_builder_type(ctx: Context, report_build_type: str) -> None:
    """
    Configure experiment report builder type.

    :param ctx: context.
    :param report_build_type: report builder type.
    """

    validate_step_type(report_build_type, "report builder")

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    report_build_type_lower = report_build_type.lower()
    experiment_config["report_builder_type"] = report_build_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Report builder type of the experiment '{experiment_name}' is set to '{report_build_type_lower}'.")
