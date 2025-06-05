from click import Context, argument, echo, pass_context

from stattest.cli.commands.common.common import (
    get_experiment_name_and_config,
    save_experiment_config,
)
from stattest.cli.commands.configure.configure import configure
from stattest.validation.cli.commands.configure.step_type.step_type import validate_step_type


@configure.command()
@argument("exec_type")
@pass_context
def executor_type(ctx: Context, exec_type: str) -> None:
    """
    Configure experiment executor type.

    :param ctx: context.
    :param exec_type: executor type.
    """

    validate_step_type(exec_type, "executor")

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    exec_type_lower = exec_type.lower()
    experiment_config["executor_type"] = exec_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Executor type of the experiment '{experiment_name}' is set to '{exec_type_lower}'.")
