from pysatl_experiment.cli.commands.build_and_run.build_and_run import build_and_run
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.cli.commands.create.create import create
from pysatl_experiment.cli.commands.criteria.criteria import available_criteria
from pysatl_experiment.cli.commands.show.show import show
from pysatl_experiment.cli.shared import cli

cli.add_command(available_criteria)
cli.add_command(create)
cli.add_command(configure)
cli.add_command(show)
cli.add_command(build_and_run)
