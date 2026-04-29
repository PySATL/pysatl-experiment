import json

from click import argument, command, echo

from pysatl_experiment.cli.commands.common.common import normalize_experiment_name, read_experiment_data


@command()
@argument("name")
def show(name: str) -> None:
    """
    Show experiment data.

    :param name: experiment name.
    """
    name = normalize_experiment_name(name)
    experiment_data = read_experiment_data(name)
    echo(json.dumps(experiment_data, indent=4))
