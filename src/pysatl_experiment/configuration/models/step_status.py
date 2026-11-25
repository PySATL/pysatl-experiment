"""Experiment pipeline step status definitions."""

from enum import Enum


class ExperimentStep(Enum):
    """Pipeline steps of an experiment."""

    GENERATION = "generation"
    EXECUTION = "execution"
    REPORT_BUILDING = "report_building"

    @classmethod
    def list(cls):
        """
        Return all enum values.

        Returns
        -------
        list[str]
            Available enum values.
        """
        return [member.value for member in cls]


class StepStatus(Enum):
    """Lifecycle statuses of an experiment step."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

    @classmethod
    def list(cls):
        """
        Return all enum values.

        Returns
        -------
        list[str]
            Available enum values.
        """
        return [member.value for member in cls]
