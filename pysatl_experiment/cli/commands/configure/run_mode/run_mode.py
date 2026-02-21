from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode


@configure.command()
@argument("mode")
@pass_context
def run_mode(ctx: Context, mode: str) -> None:
    """
    Defines the behavior for handling pre-existing experiment data.

    This enumeration controls whether an experiment should use previously
    generated or executed data found in the database or start fresh by
    overwriting any existing results for the same configuration.

    Example:
        experiment configure MyLocalRun run-mode reuse

    Args:
        ctx: The Click context object, passed automatically.
        mode: The desired run mode (e.g., 'reuse'). The value is
            case-insensitive.
    """
    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    try:
        validated_run_mode = RunMode(mode.lower())
    except ValueError:
        valid_options = [e.value for e in RunMode]
        raise BadParameter(f"Type of '{mode}' is not valid.\nPossible values are: {valid_options}.")

    experiment_config["run_mode"] = validated_run_mode.value
    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Run mode of the experiment '{experiment_name}' is set to '{validated_run_mode.value}'.")
