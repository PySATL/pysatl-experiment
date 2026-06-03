"""Shared CLI application instance and initialization utilities."""

from click import group, version_option

from pysatl_experiment.cli.commands.common.common import get_project_root


# TODO: refactor name!!


@group()
@version_option()
def cli() -> None:
    """PySATL experiments command-line interface."""
    _ensure_experiments_dir()


def _ensure_experiments_dir() -> None:
    """Create the experiments directory if it does not exist."""
    experiments_dir = get_project_root() / ".experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
