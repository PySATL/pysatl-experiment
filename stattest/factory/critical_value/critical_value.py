from stattest.configuration.experiment_config.critical_value.critical_value import (
    CriticalValueExperimentConfig,
)
from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.experiment_new.step.execution.critical_value.critical_value import (
    CriticalValueExecutionStep,
)
from stattest.experiment_new.step.generation.generation import GenerationStep
from stattest.experiment_new.step.report_building.critical_value.critical_value import (
    CriticalValueReportBuildingStep,
)
from stattest.factory.model.abstract_experiment_factory.abstract_experiment_factory import (
    IAbstractExperimentFactory,
)


class CriticalValueExperimentFactory(
    IAbstractExperimentFactory[
        GenerationStep, CriticalValueExecutionStep, CriticalValueReportBuildingStep
    ]
):
    """
    Critical value experiment factory.
    """

    pass

    def __init__(self, experiment_config: CriticalValueExperimentConfig):
        self.experiment_config = experiment_config

    def create_experiment_steps(self) -> ExperimentSteps:
        """
        Create critical value experiment steps.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_generation_step(self) -> GenerationStep:
        """
        Create generation step.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_execution_step(self) -> CriticalValueExecutionStep:
        """
        Create critical value execution step.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_report_building_step(self) -> CriticalValueReportBuildingStep:
        """
        Create critical value report building step.
        """
        raise NotImplementedError("Method is not yet implemented")
