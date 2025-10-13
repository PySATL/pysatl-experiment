from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.step_type.step_type import StepType


@configure.command()
@argument("gen_type")
@pass_context
def generator_type(ctx: Context, gen_type: str) -> None:
    """
    Set the generator type for the current experiment.

    This command configures which data generator will be used to create the
    datasets for the experiment. The type must be one of the predefined values
    in `StepType`. It updates the experiment's configuration file with the
    selected type.

    Example:
        experiment configure MySimulation generator-type standard

    Args:
        ctx: The Click context object, passed automatically.
        gen_type: The desired generator type (e.g., 'standard'). The value is
            case-insensitive.
    """

    try:
        validated_step = StepType(gen_type.lower())
    except ValueError:
        valid_options = [e.value for e in StepType]
        raise BadParameter(f"Type of '{gen_type}' is not valid.\nPossible values are: {valid_options}.")

    if validated_step == StepType.CUSTOM:
        raise BadParameter("Custom type is not supported yet.\nPlease, choose standard one")

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    gen_type_lower = gen_type.lower()
    experiment_config["generator_type"] = gen_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Generator type of the experiment '{experiment_name}' is set to '{gen_type_lower}'.")
