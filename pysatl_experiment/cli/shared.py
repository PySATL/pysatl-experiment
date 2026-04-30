from click import group, version_option

from pysatl_experiment.cli.commands.common.common import get_project_root


@group()
@version_option()
def cli() -> None:
    """
    PySATL-Experiment CLI.
    """
    _create_experiments_dir()


def _create_experiments_dir() -> None:
    """
    Create experiments directory.
    """
    experiments_dir = get_project_root() / ".experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
