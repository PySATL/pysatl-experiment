"""
Critical value experiment factory.

This module contains the factory implementation responsible for
constructing all experiment steps required for critical value
estimation.
"""

from pysatl_criterion.persistence.models.base import IDataStorage
from pysatl_criterion.persistence.models.limit_distribution import ILimitDistributionStorage, LimitDistributionQuery
from pysatl_criterion.persistence.sqlalchemy.datastorage import AlchemyLimitDistributionStorage
from typing_extensions import override

from pysatl_experiment.configuration.experiment_data.critical_value import CriticalValueExperimentData
from pysatl_experiment.experiment_execution.experiment_factory.abstract_experiment_factory import (
    AbstractExperimentFactory,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_execution_step import (
    CriticalValueExecutionStep,
    CriticalValueStepData,
)
from pysatl_experiment.experiment_execution.step.execution_step.execution_step_data import HypothesisGeneratorData
from pysatl_experiment.experiment_execution.step.generation_step.generation_step import (
    GenerationStep,
    GenerationStepContext,
)
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import GenerationData
from pysatl_experiment.experiment_execution.step.report_step.critical_value.critical_value_report_step import (
    CriticalValueReportBuildingStep,
)
from pysatl_experiment.persistence.models.experiment import IExperimentStorage
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage, RandomValuesAllQuery


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

    def _create_generation_step(self, random_values_storage: IRandomValuesStorage) -> GenerationStep:
        """
        Create a sample generation step.

        Determines which hypothesis samples are missing from storage and
        creates generation tasks only for the required number of
        additional samples.

        Parameters
        ----------
        random_values_storage : IRandomValuesStorage
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
        generator_name, generator_parameters, generator = self._get_hypothesis_generator_metadata()

        data_list = []
        for sample_size in config.sample_sizes:
            rvs_query = RandomValuesAllQuery(
                generator_code=generator_name,
                generator_parameters=generator_parameters,
                sample_size=sample_size,
            )
            existing_count = random_values_storage.get_rvs_count(rvs_query)
            missing_count = max(0, config.monte_carlo_count - existing_count)
            if missing_count > 0:
                data_list.append(
                    GenerationData(
                        generator=generator,
                        sample_size=sample_size,
                        samples_count=missing_count,
                    )
                )

        ctx = GenerationStepContext(data_list=data_list, experiment_name=self.experiment_data.experiment_name)
        return GenerationStep(ctx=ctx, random_values_storage=random_values_storage)

    def _create_execution_step(
        self,
        random_values_storage: IRandomValuesStorage,
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
        random_values_storage : IRandomValuesStorage
            Random values storage.
        result_storage : ILimitDistributionStorage
            Critical value result storage.

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
                    step_data = CriticalValueStepData(
                        statistics=statistics,
                        sample_size=sample_size,
                        criterion_parameters=criterion_config.criterion.parameters,
                    )
                    step_config.append(step_data)

        hypothesis_generator_name, hypothesis_generator_parameters, _ = self._get_hypothesis_generator_metadata()
        hypothesis_generator_data = HypothesisGeneratorData(
            generator_name=hypothesis_generator_name,
            parameters=hypothesis_generator_parameters,
        )

        return CriticalValueExecutionStep(
            experiment_id=experiment_id,
            experiment_name=self.experiment_data.experiment_name,
            hypothesis_generator_data=hypothesis_generator_data,
            step_config=step_config,
            monte_carlo_count=monte_carlo_count,
            data_storage=random_values_storage,
            result_storage=result_storage,
            storage_connection=config.storage_connection,
            parallel_workers=config.parallel_workers,
        )

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

    @override
    def _init_result_storage(self) -> AlchemyLimitDistributionStorage:
        """
        Initialize result storage.

        Creates and initializes a storage implementation corresponding
        to the configured experiment type.

        Returns
        -------
        RS
            Initialized result storage.

        Raises
        ------
        ValueError
            If the experiment type is unsupported.
        """
        storage_connection = self.experiment_data.config.storage_connection
        limit_distribution_storage = AlchemyLimitDistributionStorage(storage_connection)
        limit_distribution_storage.init()
        return limit_distribution_storage

    @override
    def _delete_sample_data(self, data_storage: IRandomValuesStorage) -> None:
        """
        Delete generated sample data.

        Selects an appropriate cleanup strategy depending on the current
        experiment type and removes stored random samples.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
        """
        self._delete_hypothesis_sample_data(data_storage)

    @override
    def _delete_results_from_storage(self, result_storage: IDataStorage) -> None:
        """
        Delete experiment results from storage.

        Creates storage queries corresponding to the current experiment
        configuration and removes all matching result records.

        Parameters
        ----------
        result_storage : IDataStorage
            Experiment result storage.
        """
        statistics_codes = []
        criteria_config = self._get_criteria_config()
        for criterion_config in criteria_config:
            statistics_codes.append(criterion_config.criterion_code)

        queries = self._create_critical_value_queries(
            statistics_codes=statistics_codes,
            sample_sizes=self.experiment_data.config.sample_sizes,
            monte_carlo_count=self.experiment_data.config.monte_carlo_count,
        )

        for query in queries:
            result_storage.delete_data(query)
