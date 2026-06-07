"""Registration of CLI commands."""

from src.pysatl_experiment.cli.commands.build_and_run import build_and_run
from src.pysatl_experiment.cli.commands.configure import configure
from src.pysatl_experiment.cli.commands.create import create
from src.pysatl_experiment.cli.commands.criteria import available_criteria
from src.pysatl_experiment.cli.commands.show import show
from src.pysatl_experiment.cli.shared import cli


cli.add_command(available_criteria)
cli.add_command(create)
cli.add_command(configure)
cli.add_command(show)
cli.add_command(build_and_run)
