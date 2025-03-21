from pysatl_experiment.experiment.configuration import ExperimentConfiguration
from pysatl_experiment.experiment.generator.generator_step import data_generation_step
from pysatl_experiment.experiment.report.report_step import execute_report_step
from pysatl_experiment.experiment.test.test_step import execute_test_step


class Experiment:
    def __init__(self, configuration: ExperimentConfiguration):
        self.__configuration = configuration

    def execute(self):
        """

        Execute experiment.

        """

        rvs_store = self.__configuration.rvs_store
        result_store = self.__configuration.result_store
        rvs_store.init()

        worker = self.__configuration.test_configuration.worker
        worker.init()

        # Generate data for alternatives
        data_generation_step(self.__configuration.alternative_configuration, rvs_store)

        # Test hypothesis
        execute_test_step(self.__configuration.test_configuration, rvs_store, result_store)

        # Generate reports
        execute_report_step(self.__configuration.report_configuration, result_store)
