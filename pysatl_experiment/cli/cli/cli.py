from pysatl_experiment.cli.commands.build_and_run.build_and_run import build_and_run
from pysatl_experiment.cli.commands.configure.alternatives.alternatives import alternatives
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.cli.commands.configure.criteria.criteria import criteria
from pysatl_experiment.cli.commands.configure.executor_type.executor_type import executor_type
from pysatl_experiment.cli.commands.configure.experiment_type.experiment_type import experiment_type
from pysatl_experiment.cli.commands.configure.generator_type.generator_type import generator_type
from pysatl_experiment.cli.commands.configure.hypothesis.hypothesis import hypothesis
from pysatl_experiment.cli.commands.configure.monte_carlo_count.monte_carlo_count import monte_carlo_count
from pysatl_experiment.cli.commands.configure.parallel_workers.parallel_workers import parallel_workers
from pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type import report_builder_type
from pysatl_experiment.cli.commands.configure.report_mode.report_mode import report_mode
from pysatl_experiment.cli.commands.configure.run_mode.run_mode import run_mode
from pysatl_experiment.cli.commands.configure.sample_sizes.sample_sizes import sample_sizes
from pysatl_experiment.cli.commands.configure.show.show import show
from pysatl_experiment.cli.commands.configure.significance_levels.significance_levels import significance_levels
from pysatl_experiment.cli.commands.configure.storage_connection.storage_connection import storage_connection
from pysatl_experiment.cli.commands.create.create import create
from pysatl_experiment.cli.shared import cli


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
cli.add_command(report_mode)
cli.add_command(parallel_workers)
cli.add_command(build_and_run)
