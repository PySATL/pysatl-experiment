from click import BadParameter, argument, command, echo

from pysatl_experiment.cli.commands.common.common import save_experiment_data
from pysatl_experiment.validation.cli.commands.common.common import if_experiment_exists


@command()
@argument("name")
def create(name: str) -> None:
    """
    Create an experiment with the given name.

    :param name: name of the experiment.
    """

    experiment_exists = if_experiment_exists(name)
    if experiment_exists:
        raise BadParameter(f"Experiment with name {name} already exists.")

    experiment_data = {
        "name": name,
        "config": {
            "generator_type": "standard",
            "executor_type": "standard",
            "report_builder_type": "standard",
            "run_mode": "reuse",
            "report_mode": "with-chart",
            "parallel_workers": 1,
        },
    }

    save_experiment_data(name, experiment_data)

    echo(f"Experiment with name '{name}' was created successfully.")
