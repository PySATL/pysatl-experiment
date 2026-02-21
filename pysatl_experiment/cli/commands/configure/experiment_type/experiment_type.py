from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType


@configure.command()
@argument("exp_type")
@pass_context
def experiment_type(ctx: Context, exp_type: str) -> None:
    """
    Set the type for the current experiment.

    This command configures the main objective of the experiment, such as
    'power' for power analysis or 'critical_value' for calculating critical
    values. The chosen type affects which other configuration parameters are
    valid and required.

    Example:
        experiment configure MyPowerAnalysis experiment-type power

    Args:
        ctx: The Click context object, passed automatically.
        exp_type: The desired experiment type (e.g., 'power', 'time_complexity').
            The value must match one of the predefined types in `ExperimentType`
            and is case-insensitive.
    """
    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    try:
        validated_experiment_type = ExperimentType(exp_type.lower())
    except ValueError:
        valid_options = [e.value for e in ExperimentType]
        raise BadParameter(f"Type of '{exp_type}' is not valid.\nPossible values are: {valid_options}.")

    experiment_config["experiment_type"] = validated_experiment_type.value

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Type of the experiment '{experiment_name}' is set to '{validated_experiment_type.value}'.")
