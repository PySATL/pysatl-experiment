from click import Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure


@configure.command()
@argument("storage_type")
@pass_context
def storage_type(ctx: Context, store_type: str) -> None:
    """
    Configure storage type.

    :param ctx: context.
    :param store_type: storage type.
    """

    # TODO: add support for remote storage

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    # TODO
    storage_type_lower = store_type.lower()
    experiment_config["storage_type"] = storage_type_lower
    # TODO

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Report builder type of the experiment '{experiment_name}' is set to '{storage_type_lower}'.")
