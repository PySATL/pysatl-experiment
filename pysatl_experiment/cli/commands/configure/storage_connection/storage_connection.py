from click import Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure


@configure.command()
@argument("connection")
@pass_context
def storage_connection(ctx: Context, connection: str) -> None:
    """
    Configure storage connection.

    :param ctx: context.
    :param connection: storage connection. Example: postgresql://postgres:postgres@localhost/pysatl
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_config["storage_connection"] = connection

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Storage connection of the experiment {experiment_name} is set to '{connection}'.")
