from stattest.configuration.experiment_config.power.power import PowerExperimentConfig
from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.experiment_new.step.execution.power.power import PowerExecutionStep
from stattest.experiment_new.step.generation.generation import GenerationStep
from stattest.experiment_new.step.report_building.power.power import PowerReportBuildingStep
from stattest.factory.model.abstract_experiment_factory.abstract_experiment_factory import (
    IAbstractExperimentFactory,
)


class PowerExperimentFactory(
    IAbstractExperimentFactory[GenerationStep, PowerExecutionStep, PowerReportBuildingStep]
):
    """
    Power experiment factory.
    """

    pass

    def __init__(self, experiment_config: PowerExperimentConfig):
        self.experiment_config = experiment_config

    def create_experiment_steps(self) -> ExperimentSteps:
        """
        Create power experiment steps.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_generation_step(self) -> GenerationStep:
        """
        Create generation step.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_execution_step(self) -> PowerExecutionStep:
        """
        Create power execution step.
        """
        raise NotImplementedError("Method is not yet implemented")

    def _create_report_building_step(self) -> PowerReportBuildingStep:
        """
        Create power report building step.
        """
        raise NotImplementedError("Method is not yet implemented")
