"""
Critical value experiment factory.

This module contains the factory implementation responsible for
constructing all experiment steps required for critical value
estimation.
"""

from pysatl_criterion.persistence.models.limit_distribution import ILimitDistributionStorage, LimitDistributionQuery

from pysatl_experiment.configuration.experiment_data.critical_value import CriticalValueExperimentData
from pysatl_experiment.experiment.step.execution.common.hypothesis_generator_data import (  # noqa: E501
    HypothesisGeneratorData,
)
from pysatl_experiment.experiment.step.execution.critical_value import CriticalValueExecutionStep, CriticalValueStepData
from pysatl_experiment.experiment.step.generation import GenerationStep, GenerationStepData
from pysatl_experiment.experiment.step.report_building.critical_value import CriticalValueReportBuildingStep
from pysatl_experiment.factory.model.abstract_experiment_factory import AbstractExperimentFactory
from pysatl_experiment.persistence.model.experiment import IExperimentStorage
from pysatl_experiment.persistence.model.random_values import IRandomValuesStorage, RandomValuesAllQuery


class CriticalValueExperimentFactory(
    AbstractExperimentFactory[
        CriticalValueExperimentData,
        GenerationStep,
        CriticalValueExecutionStep,
        CriticalValueReportBuildingStep,
        ILimitDistributionStorage,
    ]
):
    """
    Factory for critical value experiments.

    Creates generation, execution and report-building steps required
    for Monte Carlo estimation of critical values for statistical
    criteria.
    """

    def __init__(self, experiment_data: CriticalValueExperimentData):
        """
        Initialize the factory.

        Parameters
        ----------
        experiment_data : CriticalValueExperimentData
            Critical value experiment configuration and execution
            metadata.
        """
        super().__init__(experiment_data)

    def _create_generation_step(self, data_storage: IRandomValuesStorage) -> GenerationStep:
        """
        Create a sample generation step.

        Determines which hypothesis samples are missing from storage and
        creates generation tasks only for the required number of
        additional samples.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.

        Returns
        -------
        GenerationStep
            Configured generation step.

        Notes
        -----
        Existing samples are reused whenever possible. Only missing
        samples required to reach the configured Monte Carlo count are
        generated.
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
        result_storage: ILimitDistributionStorage,
        experiment_storage: IExperimentStorage,
    ) -> CriticalValueExecutionStep:
        """
        Create a critical value execution step.

        Determines which criterion and sample-size combinations do not
        yet have stored critical value results and prepares execution
        tasks for those combinations.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
        result_storage : ILimitDistributionStorage
            Critical value result storage.
        experiment_storage : IExperimentStorage
            Experiment metadata storage.

        Returns
        -------
        CriticalValueExecutionStep
            Configured execution step.

        Notes
        -----
        Existing critical value distributions are reused and excluded
        from execution planning.
        """
        config = self.experiment_data.config
        experiment_id = self._get_experiment_id(experiment_storage)
        monte_carlo_count = config.monte_carlo_count
        criteria_config = self._get_criteria_config()

        step_config: list[CriticalValueStepData] = []
        for criterion_config in criteria_config:
            for sample_size in config.sample_sizes:
                query = LimitDistributionQuery(
                    criterion_code=criterion_config.criterion_code,
                    criterion_parameters=criterion_config.criterion.parameters,
                    sample_size=sample_size,
                    monte_carlo_count=monte_carlo_count,
                )
                result = result_storage.get_data(query)
                if result is None:
                    statistics = criterion_config.statistics_class_object
                    step_data = CriticalValueStepData(statistics=statistics, sample_size=sample_size)
                    step_config.append(step_data)

        hypothesis_generator_name, hypothesis_generator_parameters, _ = self._get_hypothesis_generator_metadata()
        hypothesis_generator_data = HypothesisGeneratorData(
            generator_name=hypothesis_generator_name,
            parameters=hypothesis_generator_parameters,
        )

        execution_step = CriticalValueExecutionStep(
            experiment_id=experiment_id,
            hypothesis_generator_data=hypothesis_generator_data,
            step_config=step_config,
            monte_carlo_count=monte_carlo_count,
            data_storage=data_storage,
            result_storage=result_storage,
            storage_connection=config.storage_connection,
            parallel_workers=config.parallel_workers,
        )

        # TODO: template method with other factories??

        return execution_step

    def _create_report_building_step(
        self, result_storage: ILimitDistributionStorage
    ) -> CriticalValueReportBuildingStep:
        """
        Create a report-building step.

        Configures report generation using stored critical value
        distributions, significance levels and sample sizes.

        Parameters
        ----------
        result_storage : ILimitDistributionStorage
            Critical value result storage.

        Returns
        -------
        CriticalValueReportBuildingStep
            Configured report-building step.
        """
        return CriticalValueReportBuildingStep(
            report_name=self.experiment_data.name,
            criteria_config=self._get_criteria_config(),
            significance_levels=self.experiment_data.config.significance_levels,
            sample_sizes=self.experiment_data.config.sample_sizes,
            monte_carlo_count=self.experiment_data.config.monte_carlo_count,
            result_storage=result_storage,
            results_path=self.experiment_data.results_path,
            with_chart=self.experiment_data.config.report_mode,
        )
