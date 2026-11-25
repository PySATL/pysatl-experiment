"""Experiment steps status model."""

from dataclasses import dataclass

from pysatl_experiment.configuration.models.step_status import StepStatus


@dataclass
class StepsStatus:
    """
    Lifecycle statuses of experiment steps.

    Attributes
    ----------
    generation_status : StepStatus
        Status of the sample generation step.
    execution_status : StepStatus
        Status of the experiment execution step.
    report_building_status : StepStatus
        Status of the report generation step.
    """

    generation_status: StepStatus = StepStatus.PENDING
    execution_status: StepStatus = StepStatus.PENDING
    report_building_status: StepStatus = StepStatus.PENDING
