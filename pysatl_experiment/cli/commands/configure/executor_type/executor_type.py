from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.step_type.step_type import StepType


@configure.command()
@argument("exec_type")
@pass_context
def executor_type(ctx: Context, exec_type: str) -> None:
    """
    Set the executor type for the current experiment.

    This command configures which executor will be used for the experiment's
    execution step. The type must be one of the predefined values in `StepType`.
    It updates the experiment's configuration file with the provided value.

    Example:
        experiment configure EXPERIMENT_NAME executor-type standard
    Args:
        ctx: The Click context object, passed automatically.
        exec_type: The desired executor type (e.g., 'standard'). The value is
            case-insensitive.
    """
    try:
        validated_step = StepType(exec_type.lower())
    except ValueError:
        valid_options = [e.value for e in StepType]
        raise BadParameter(f"Type of '{exec_type}' is not valid.\nPossible values are: {valid_options}.")

    if validated_step == StepType.CUSTOM:
        raise BadParameter("Custom type is not supported yet.\nPlease, choose standard one")

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    exec_type_lower = exec_type.lower()
    experiment_config["executor_type"] = exec_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Executor type of the experiment '{experiment_name}' is set to '{exec_type_lower}'.")
