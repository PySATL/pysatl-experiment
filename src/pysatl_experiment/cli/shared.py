"""Shared CLI application instance and initialization utilities."""

from click import group, version_option

from pysatl_experiment.system.gc_setup import gc_set_threshold
from pysatl_experiment.utils.files_utils import ensure_experiment_dir


# TODO: refactor name!!


@group()
@version_option()
def cli() -> None:
    """PySATL experiments command-line interface."""
    gc_set_threshold()
    ensure_experiment_dir()
