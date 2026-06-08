"""
Power experiment factory.

This module contains the factory implementation responsible for
constructing experiment steps required to estimate statistical power
for goodness-of-fit criteria under alternative distributions.
"""

from pysatl_experiment.configuration.experiment_data.power import PowerExperimentData
from pysatl_experiment.experiment_execution.step.execution.power import PowerExecutionStep, PowerStepData
from pysatl_experiment.experiment_execution.step.generation import GenerationStep, GenerationStepData
from pysatl_experiment.experiment_execution.step.report_building.power import PowerReportBuildingStep
from pysatl_experiment.factory.abstract_experiment_factory import AbstractExperimentFactory
from pysatl_experiment.persistence.models.experiment import IExperimentStorage
from pysatl_experiment.persistence.models.power import IPowerStorage, PowerQuery
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage, RandomValuesAllQuery


class PowerExperimentFactory(
    AbstractExperimentFactory[
        PowerExperimentData,
        GenerationStep,
        PowerExecutionStep,
        PowerReportBuildingStep,
        IPowerStorage,
    ]
):
    """
    Factory for statistical power experiments.

    Creates generation, execution and report-building steps required
    for statistical power estimation under configured alternative
    distributions.
    """

    def __init__(self, experiment_data: PowerExperimentData):
        """
        Initialize the factory.

        Parameters
        ----------
        experiment_data : PowerExperimentData
            Power experiment configuration and execution metadata.
        """
        super().__init__(experiment_data)

    def _create_generation_step(self, data_storage: IRandomValuesStorage) -> GenerationStep:
        """
        Create a sample generation step.

        Determines which samples corresponding to alternative
        distributions are missing from storage and creates generation
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

        step_config = []
        for sample_size in config.sample_sizes:
            for alternative in config.alternatives:
                generator_name = alternative.generator_name
                generator_parameters = alternative.parameters
                query = RandomValuesAllQuery(
                    generator_name=generator_name,
                    generator_parameters=generator_parameters,
                    sample_size=sample_size,
                )
                rvs_count = data_storage.get_rvs_count(query)
                if rvs_count < monte_carlo_count:
                    needed_rvs_count = monte_carlo_count - rvs_count
                    generator = self._get_generator_class_object(generator_name, generator_parameters)
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
        result_storage: IPowerStorage,
        experiment_storage: IExperimentStorage,
    ) -> PowerExecutionStep:
        """
        Create a statistical power execution step.

        Determines which combinations of criterion, sample size,
        significance level and alternative distribution do not yet
        have stored power estimates and prepares execution tasks for
        those combinations.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
        result_storage : IPowerStorage
            Power result storage.
        experiment_storage : IExperimentStorage
            Experiment metadata storage.

        Returns
        -------
        PowerExecutionStep
            Configured execution step.
        """
        config = self.experiment_data.config
        experiment_id = self._get_experiment_id(experiment_storage)
        monte_carlo_count = config.monte_carlo_count
        storage_connection = config.storage_connection

        criteria_config = self._get_criteria_config()

        step_config: list[PowerStepData] = []
        for criterion_config in criteria_config:
            for sample_size in config.sample_sizes:
                for alternative in config.alternatives:
                    for significance_level in config.significance_levels:
                        query = PowerQuery(
                            criterion_code=criterion_config.criterion_code,
                            criterion_parameters=criterion_config.criterion.parameters,
                            sample_size=sample_size,
                            monte_carlo_count=monte_carlo_count,
                            alternative_code=alternative.generator_name,
                            alternative_parameters=alternative.parameters,
                            significance_level=significance_level,
                        )
                        result = result_storage.get_data(query)
                        if result is None:
                            statistics = criterion_config.statistics_class_object
                            step_data = PowerStepData(
                                statistics=statistics,
                                sample_size=sample_size,
                                alternative=alternative,
                                significance_level=significance_level,
                            )
                            step_config.append(step_data)

        execution_step = PowerExecutionStep(
            experiment_id=experiment_id,
            step_config=step_config,
            monte_carlo_count=monte_carlo_count,
            data_storage=data_storage,
            result_storage=result_storage,
            storage_connection=storage_connection,
            parallel_workers=config.parallel_workers,
        )

        return execution_step

    def _create_report_building_step(
        self,
        result_storage: IPowerStorage,
    ) -> PowerReportBuildingStep:
        """
        Create a report-building step.

        Configures report generation using stored power estimates,
        significance levels, sample sizes and alternative
        distributions.

        Parameters
        ----------
        result_storage : IPowerStorage
            Power result storage.

        Returns
        -------
        PowerReportBuildingStep
            Configured report-building step.
        """
        return PowerReportBuildingStep(
            report_name=self.experiment_data.name,
            criteria_config=self._get_criteria_config(),
            significance_levels=self.experiment_data.config.significance_levels,
            alternatives=self.experiment_data.config.alternatives,
            sample_sizes=self.experiment_data.config.sample_sizes,
            monte_carlo_count=self.experiment_data.config.monte_carlo_count,
            result_storage=result_storage,
            results_path=self.experiment_data.results_path,
            with_chart=self.experiment_data.config.report_mode,
        )
