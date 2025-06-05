from click import Context, argument, echo, pass_context

from stattest.cli.commands.common.common import (
    get_experiment_name_and_config,
    save_experiment_config,
)
from stattest.cli.commands.configure.configure import configure
from stattest.validation.cli.commands.configure.experiment_type.experiment_type import (
    validate_experiment_type,
)


@configure.command()
@argument("exp_type")
@pass_context
def experiment_type(ctx: Context, exp_type: str) -> None:
    """
    Configure experiment type.

    :param ctx: context.
    :param exp_type: experiment type.
    """

    validate_experiment_type(exp_type)

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    exp_type_lower = exp_type.lower()
    experiment_config["experiment_type"] = exp_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Type of the experiment '{experiment_name}' is set to '{exp_type_lower}'.")
