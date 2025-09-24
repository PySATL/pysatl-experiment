from pathlib import Path

from click import group, version_option


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
    # pysatl-experiment/.experiments
    folder_path = Path(__file__).resolve().parents[2] / ".experiments"
    folder_path.mkdir(parents=False, exist_ok=True)
