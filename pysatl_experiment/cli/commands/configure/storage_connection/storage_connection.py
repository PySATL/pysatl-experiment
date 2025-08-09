from click import Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import (
    create_storage_path,
    get_experiment_name_and_config,
    save_experiment_config,
)
from pysatl_experiment.cli.commands.configure.configure import configure


@configure.command()
@argument("connection")
@pass_context
def storage_connection(ctx: Context, connection: str) -> None:
    """
    Configure storage connection.

    :param ctx: context.
    :param connection: storage connection.
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    storage_path = create_storage_path(connection)
    experiment_config["storage_connection"] = storage_path

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Storage connection of the experiment {experiment_name} is set to '{storage_path}'.")
