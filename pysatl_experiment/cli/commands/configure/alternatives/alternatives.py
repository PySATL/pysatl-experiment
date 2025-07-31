from click import ClickException, Context, echo, option, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.validation.cli.commands.configure.alternatives.alternatives import validate_alternatives


@configure.command()
@option("--alt", multiple=True, help="Example: 'generator_name param1 param2'.")
@pass_context
def alternatives(ctx: Context, alt: tuple[str]) -> None:
    """
    Configure experiment alternatives.

    :param ctx: context.
    :param alt: alternatives.
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_type = experiment_config.get("experiment_type")
    if experiment_type is None:
        raise ClickException(
            f"Experiment type is not configured.\n"
            f"Please, configure it first by calling "
            f"'experiment configure {experiment_name} experiment-type <exp_type>'."
        )

    alternatives_data = validate_alternatives(alt, experiment_type)
    experiment_config["alternatives"] = alternatives_data

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Alternatives of the experiment '{experiment_name}' are successfully set to {alternatives_data}.")
