"""Experiment execution state model."""

from dataclasses import dataclass


@dataclass
class StepsDone:  # TODO: check more??
    """
    Flags indicating completed experiment steps.

    Attributes
    ----------
    is_generation_step_done : bool
        Whether the sample generation step has completed.
    is_execution_step_done : bool
        Whether the experiment execution step has completed.
    is_report_building_step_done : bool
        Whether the report generation step has completed.
    """

    is_generation_step_done: bool
    is_execution_step_done: bool
    is_report_building_step_done: bool
