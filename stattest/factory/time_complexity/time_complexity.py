from stattest.configuration.experiment_data.time_complexity.time_complexity import (
    TimeComplexityExperimentData,
)
from stattest.experiment_new.step.execution.common.hypothesis_generator_data.hypothesis_generator_data import (
    HypothesisGeneratorData,
)
from stattest.experiment_new.step.execution.time_complexity.time_complexity import (
    TimeComplexityExecutionStep,
    TimeComplexityStepData,
)
from stattest.experiment_new.step.generation.generation import GenerationStep, GenerationStepData
from stattest.experiment_new.step.report_building.time_complexity.time_complexity import (
    TimeComplexityReportBuildingStep,
)
from stattest.factory.model.abstract_experiment_factory.abstract_experiment_factory import (
    AbstractExperimentFactory,
)
from stattest.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllQuery,
)
from stattest.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityQuery,
)


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
    Time complexity experiment factory.
    """

    def __init__(self, experiment_data: TimeComplexityExperimentData):
        super().__init__(experiment_data)

    def _create_generation_step(self, data_storage: IRandomValuesStorage) -> GenerationStep:
        """
        Create generation step.

        :param data_storage: data storage.

        :return: time complexity generation step.
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
        self, data_storage: IRandomValuesStorage, result_storage: ITimeComplexityStorage
    ) -> TimeComplexityExecutionStep:
        """
        Create time complexity execution step.

        :param data_storage: data storage.
        :param result_storage: result time complexity storage.

        :return: time complexity execution step.
        """

        config = self.experiment_data.config
        experiment_id = self._get_experiment_id()
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
                    step_data = TimeComplexityStepData(
                        statistics=statistics, sample_size=sample_size
                    )
                    step_config.append(step_data)

        hypothesis_generator_name, hypothesis_generator_parameters, _ = (
            self._get_hypothesis_generator_metadata()
        )
        hypothesis_generator_data = HypothesisGeneratorData(
            generator_name=hypothesis_generator_name, parameters=hypothesis_generator_parameters
        )

        execution_step = TimeComplexityExecutionStep(
            experiment_id=experiment_id,
            hypothesis_generator_data=hypothesis_generator_data,
            step_config=step_config,
            monte_carlo_count=monte_carlo_count,
            data_storage=data_storage,
            result_storage=result_storage,
        )

        return execution_step

    def _create_report_building_step(
        self, result_storage: ITimeComplexityStorage
    ) -> TimeComplexityReportBuildingStep:
        """
        Create time complexity report building step.

        :param result_storage: result time complexity storage.

        :return: time complexity report building step.
        """

        criteria_config = self._get_criteria_config()
        sample_sizes = self.experiment_data.config.sample_sizes
        monte_carlo_count = self.experiment_data.config.monte_carlo_count
        results_path = self.experiment_data.results_path

        report_building_step = TimeComplexityReportBuildingStep(
            criteria_config=criteria_config,
            sample_sizes=sample_sizes,
            monte_carlo_count=monte_carlo_count,
            result_storage=result_storage,
            results_path=results_path,
        )

        return report_building_step
