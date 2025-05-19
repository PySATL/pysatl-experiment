import logging
import signal
from typing import Any


logger = logging.getLogger(__name__)


def start_experiment(args: dict[str, Any]) -> int:
    """
    Main entry point for experiment mode
    """
    # Import here to avoid loading worker module when it's not used
    from stattest.configuration.configuration_parser import ConfigurationParser
    from stattest.experiment import Experiment

    def term_handler(signum, frame):
        # Raise KeyboardInterrupt - so we can handle it in the same way as Ctrl-C
        raise KeyboardInterrupt()

    # Create and run worker
    try:
        experiment_configurations = ConfigurationParser.parse_configs(args.get("config"))

        for experiment_configuration in experiment_configurations:
            experiment = Experiment(experiment_configuration)

            # Execute experiment
            experiment.execute()

        signal.signal(signal.SIGTERM, term_handler)
    finally:
        logger.info("calling exit")
    return 0
