from click import ClickException, Context, echo, option, pass_context
from pydantic import ValidationError

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.validation.cli.schemas.alternative import AlternativesConfig


@configure.command()
@option("--alt", multiple=True, help="Example: 'generator_name param1 param2'.")
@pass_context
def alternatives(ctx: Context, alt: tuple[str]) -> None:
    """
    Set the alternative hypotheses for the current experiment.

    This command configures one or more alternative hypotheses, which are
    necessary for 'power' experiments. It requires the experiment type to be
    set beforehand and will raise an error if alternatives are provided for an
    incompatible experiment type.

    Each alternative must be provided with a separate `--alt` option.

    Example:
        experiment configure MyPowerAnalysis alternatives --alt "Normal 1.0 0.5" --alt "Cauchy 0 2"

    Args:
        ctx: The Click context object, passed automatically.
        alt: A tuple of strings, where each string defines one alternative
            in the format "generator_name param1 param2 ...".
    """
    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_type = experiment_config.get("experiment_type")
    if experiment_type is None:
        raise ClickException(
            f"Experiment type is not configured.\n"
            f"Please, configure it first by calling "
            f"'experiment configure {experiment_name} experiment-type <exp_type>'."
        )

    try:
        validated_config = AlternativesConfig(experiment_type=experiment_type, alternatives=list(alt))

        alternatives_data = validated_config.model_dump().get("alternatives", [])

    except ValidationError as e:
        raise ClickException(str(e))

    experiment_config["alternatives"] = alternatives_data

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Alternatives of the experiment '{experiment_name}' are successfully set.")
    if alternatives_data:
        echo("Configured alternatives:")
        for alt_item in alternatives_data:
            params_str = " ".join(map(str, alt_item.get("parameters", [])))
            echo(f"  - {alt_item.get('generator_name')} {params_str}")
