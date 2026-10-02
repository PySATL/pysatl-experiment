"""CLI command using the configuration loading and validation pipeline."""

from click import BadParameter, ClickException, argument, command, option
from click_loglevel import LogLevel

from pysatl_experiment.configuration.config_loader import read_raw_experiment_config
from pysatl_experiment.configuration.validation import (
    ConfigReadError,
    ConfigValidationError,
    validate_experiment_config,
)
from pysatl_experiment.experiment_execution.build import build_experiment
from pysatl_experiment.experiment_execution.dependencies import ExperimentDependencyError
from pysatl_experiment.experiment_execution.registry import (
    ExperimentPluginError,
    ExperimentRegistryError,
    create_default_experiment_registry,
)
from pysatl_experiment.experiment_execution.runner import Experiment
from pysatl_experiment.loggers import setup_logging
from pysatl_experiment.utils.experiment_utils import is_experiment_exists
from pysatl_experiment.utils.files_utils import ensure_experiment_conf


@command()
@argument("name")
@option("-l", "--log-level", type=LogLevel(), default="WARNING", help="Set logging level", show_default=True)
@option("--log-file", help="Set logging file")
def build_and_run(name: str, log_level: int, log_file: str) -> None:
    """Validate, prepare and plan a named experiment through its registry, then run its steps."""
    if not is_experiment_exists(name):
        raise BadParameter(f"Experiment with name {name} does not exist.")
    setup_logging({}, log_level, log_file)
    try:
        raw = read_raw_experiment_config(ensure_experiment_conf(name))
        registry = create_default_experiment_registry()
        config = validate_experiment_config(raw, registry=registry)
        steps = build_experiment(config, registry=registry)
    except (
        ConfigReadError,
        ConfigValidationError,
        ExperimentDependencyError,
        ExperimentPluginError,
        ExperimentRegistryError,
    ) as error:
        raise ClickException(str(error)) from error
    Experiment(steps).run_experiment()
