from stattest.experiment.configuration.configuration import ExperimentConfiguration
from stattest.experiment.generator.generator_step import data_generation_step
from stattest.experiment.report.report_step import execute_report_step
from stattest.experiment.test.test_step import execute_test_step


class Experiment:
    def __init__(self, configuration: ExperimentConfiguration or str):
        self.__configuration = configuration

    def execute(self):
        """

        Execute experiment.

        """

        rvs_store = self.__configuration.rvs_store

        # Generate data for alternatives
        data_generation_step(self.__configuration.alternative_configuration, rvs_store)

        # Test hypothesis
        execute_test_step(self.__configuration.test_configuration, rvs_store)

        # Generate reports
        execute_report_step(self.__configuration.report_configuration)
