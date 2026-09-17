"""Shared CLI application instance and initialization utilities."""

from click import group, version_option

from pysatl_experiment.utils.files_utils import ensure_experiment_dir


# TODO: refactor name!!


@group()
@version_option()
def cli() -> None:
    """PySATL experiments command-line interface."""
    ensure_experiment_dir()
