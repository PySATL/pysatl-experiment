from stattest.configuration.experiment_config.critical_value.critical_value import (
    CriticalValueExperimentConfig,
)
from stattest.configuration.experiment_config.time_complexity.time_complexity import TimeComplexityExperimentConfig
from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.experiment_new.step.execution.time_complexity.time_complexity import (
    TimeComplexityExecutionStep,
)
from stattest.experiment_new.step.generation.generation import GenerationStep
from stattest.experiment_new.step.report_building.time_complexity.time_complexity import (
    TimeComplexityReportBuildingStep,
)
from stattest.factory.model.abstract_experiment_factory.abstract_experiment_factory import (
    IAbstractExperimentFactory,
)


class TimeComplexityExperimentFactory(
    IAbstractExperimentFactory[
        GenerationStep, TimeComplexityExecutionStep, TimeComplexityReportBuildingStep
    ]
):
    """
    Time complexity experiment factory.
    """

    pass

    def __init__(self, experiment_config: TimeComplexityExperimentConfig):
        self.experiment_config = experiment_config

    def create_experiment_steps(self) -> ExperimentSteps:
        """
        Create time complexity experiment steps.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_generation_step(self) -> GenerationStep:
        """
        Create generation step.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_execution_step(self) -> TimeComplexityExecutionStep:
        """
        Create time complexity execution step.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_report_building_step(self) -> TimeComplexityReportBuildingStep:
        """
        Create time complexity report building step.
        """
        raise NotImplementedError("Method is not yet implemented")
