from pathlib import Path

from click import group, version_option

from stattest.cli.commands.build_and_run.build_and_run import build_and_run
from stattest.cli.commands.configure.alternatives.alternatives import alternatives
from stattest.cli.commands.configure.configure import configure
from stattest.cli.commands.configure.criteria.criteria import criteria
from stattest.cli.commands.configure.executor_type.executor_type import executor_type
from stattest.cli.commands.configure.experiment_type.experiment_type import experiment_type
from stattest.cli.commands.configure.generator_type.generator_type import generator_type
from stattest.cli.commands.configure.hypothesis.hypothesis import hypothesis
from stattest.cli.commands.configure.monte_carlo_count.monte_carlo_count import monte_carlo_count
from stattest.cli.commands.configure.report_builder_type.report_builder_type import (
    report_builder_type,
)
from stattest.cli.commands.configure.run_mode.run_mode import run_mode
from stattest.cli.commands.configure.sample_sizes.sample_sizes import sample_sizes
from stattest.cli.commands.configure.show.show import show
from stattest.cli.commands.configure.significance_levels.significance_levels import (
    significance_levels,
)
from stattest.cli.commands.configure.storage_connection.storage_connection import storage_connection
from stattest.cli.commands.create.create import create


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
    folder_path = Path(__file__).resolve().parents[3] / ".experiments"
    folder_path.mkdir(parents=False, exist_ok=True)


cli.add_command(create)
cli.add_command(configure)
cli.add_command(experiment_type)
cli.add_command(show)
cli.add_command(storage_connection)
cli.add_command(run_mode)
cli.add_command(hypothesis)
cli.add_command(generator_type)
cli.add_command(executor_type)
cli.add_command(report_builder_type)
cli.add_command(sample_sizes)
cli.add_command(monte_carlo_count)
cli.add_command(significance_levels)
cli.add_command(criteria)
cli.add_command(alternatives)
cli.add_command(build_and_run)
