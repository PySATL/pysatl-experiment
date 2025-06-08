from click import Context, argument, echo, pass_context

from stattest.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from stattest.cli.commands.configure.configure import configure
from stattest.validation.cli.commands.configure.step_type.step_type import validate_step_type


@configure.command()
@argument("gen_type")
@pass_context
def generator_type(ctx: Context, gen_type: str) -> None:
    """
    Configure experiment generator type.

    :param ctx: context.
    :param gen_type: generator type.
    """

    validate_step_type(gen_type, "generator")

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    gen_type_lower = gen_type.lower()
    experiment_config["generator_type"] = gen_type_lower

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Generator type of the experiment '{experiment_name}' is set to '{gen_type_lower}'.")
