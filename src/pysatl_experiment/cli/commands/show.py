"""CLI command for displaying experiment data."""

import json

from click import argument, command, echo

from src.pysatl_experiment.cli.commands.common import normalize_experiment_name, read_experiment_data


@command()
@argument("name")
def show(name: str) -> None:
    """
    Show experiment data.

    Parameters
    ----------
    name : str
        Experiment name.
    """
    name = normalize_experiment_name(name)
    experiment_data = read_experiment_data(name)

    echo(json.dumps(experiment_data, indent=4))
