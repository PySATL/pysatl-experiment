"""
Time complexity experiment factory.

This module contains the factory implementation responsible for
constructing experiment steps required to evaluate computational
complexity of statistical criteria.
"""

from src.pysatl_experiment.configuration.experiment_data.time_complexity import TimeComplexityExperimentData
from src.pysatl_experiment.experiment.step.execution.common.hypothesis_generator_data import (  # noqa: E501
    HypothesisGeneratorData,
)
from src.pysatl_experiment.experiment.step.execution.time_complexity import (
    TimeComplexityExecutionStep,
    TimeComplexityStepData,
)
from src.pysatl_experiment.experiment.step.generation import GenerationStep, GenerationStepData
from src.pysatl_experiment.experiment.step.report_building.time_complexity import TimeComplexityReportBuildingStep
from src.pysatl_experiment.factory.model.abstract_experiment_factory import AbstractExperimentFactory
from src.pysatl_experiment.persistence.model.experiment import IExperimentStorage
from src.pysatl_experiment.persistence.model.random_values import IRandomValuesStorage, RandomValuesAllQuery
from src.pysatl_experiment.persistence.model.time_complexity import ITimeComplexityStorage, TimeComplexityQuery


class TimeComplexityExperimentFactory(
    AbstractExperimentFactory[
        TimeComplexityExperimentData,
        GenerationStep,
        TimeComplexityExecutionStep,
        TimeComplexityReportBuildingStep,
        ITimeComplexityStorage,
    ]
):
    """
    Factory for time complexity experiments.

    Creates generation, execution and report-building steps required
    for measuring execution time of statistical criteria for different
    sample sizes.
    """

    def __init__(self, experiment_data: TimeComplexityExperimentData):
        """
        Initialize the factory.

        Parameters
        ----------
        experiment_data : TimeComplexityExperimentData
            Time complexity experiment configuration and execution
            metadata.
        """
        super().__init__(experiment_data)

    def _create_generation_step(self, data_storage: IRandomValuesStorage) -> GenerationStep:
        """
        Create a sample generation step.

        Determines which samples generated under the configured null
        hypothesis are missing from storage and creates generation
        tasks only for the required number of additional samples.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.

        Returns
        -------
        GenerationStep
            Configured generation step.
        """
        config = self.experiment_data.config
        monte_carlo_count = config.monte_carlo_count
        generator_name, generator_parameters, generator = self._get_hypothesis_generator_metadata()

        step_config = []

        for sample_size in config.sample_sizes:
            query = RandomValuesAllQuery(
                generator_name=generator_name,
                generator_parameters=generator_parameters,
                sample_size=sample_size,
            )
            rvs_count = data_storage.get_rvs_count(query)
            if rvs_count < monte_carlo_count:
                needed_rvs_count = monte_carlo_count - rvs_count
                step_data = GenerationStepData(
                    generator=generator,
                    generator_name=generator_name,
                    generator_parameters=generator_parameters,
                    sample_size=sample_size,
                    count=needed_rvs_count,
                )
                step_config.append(step_data)
            else:
                continue

        generation_step = GenerationStep(step_config=step_config, data_storage=data_storage)

        return generation_step

    def _create_execution_step(
        self,
        data_storage: IRandomValuesStorage,
        result_storage: ITimeComplexityStorage,
        experiment_storage: IExperimentStorage,
    ) -> TimeComplexityExecutionStep:
        """
        Create a time complexity execution step.

        Determines which criterion and sample-size combinations do not
        yet have stored timing measurements and prepares execution tasks
        for those combinations.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
        result_storage : ITimeComplexityStorage
            Time complexity result storage.
        experiment_storage : IExperimentStorage
            Experiment metadata storage.

        Returns
        -------
        TimeComplexityExecutionStep
            Configured execution step.
        """
        config = self.experiment_data.config
        experiment_id = self._get_experiment_id(experiment_storage)
        monte_carlo_count = config.monte_carlo_count
        criteria_config = self._get_criteria_config()

        step_config: list[TimeComplexityStepData] = []
        for criterion_config in criteria_config:
            for sample_size in config.sample_sizes:
                query = TimeComplexityQuery(
                    criterion_code=criterion_config.criterion_code,
                    criterion_parameters=criterion_config.criterion.parameters,
                    sample_size=sample_size,
                    monte_carlo_count=monte_carlo_count,
                )
                result = result_storage.get_data(query)
                if result is None:
                    statistics = criterion_config.statistics_class_object
                    step_data = TimeComplexityStepData(statistics=statistics, sample_size=sample_size)
                    step_config.append(step_data)

        hypothesis_generator_name, hypothesis_generator_parameters, _ = self._get_hypothesis_generator_metadata()
        hypothesis_generator_data = HypothesisGeneratorData(
            generator_name=hypothesis_generator_name,
            parameters=hypothesis_generator_parameters,
        )

        execution_step = TimeComplexityExecutionStep(
            experiment_id=experiment_id,
            hypothesis_generator_data=hypothesis_generator_data,
            step_config=step_config,
            monte_carlo_count=monte_carlo_count,
            data_storage=data_storage,
            result_storage=result_storage,
            storage_connection=config.storage_connection,
            parallel_workers=config.parallel_workers,
        )

        return execution_step

    def _create_report_building_step(self, result_storage: ITimeComplexityStorage) -> TimeComplexityReportBuildingStep:
        """
        Create a report-building step.

        Configures report generation using stored execution time
        measurements and configured sample sizes.

        Parameters
        ----------
        result_storage : ITimeComplexityStorage
            Time complexity result storage.

        Returns
        -------
        TimeComplexityReportBuildingStep
            Configured report-building step.
        """
        return TimeComplexityReportBuildingStep(
            report_name=self.experiment_data.name,
            criteria_config=self._get_criteria_config(),
            sample_sizes=self.experiment_data.config.sample_sizes,
            monte_carlo_count=self.experiment_data.config.monte_carlo_count,
            result_storage=result_storage,
            results_path=self.experiment_data.results_path,
            with_chart=self.experiment_data.config.report_mode,
        )
