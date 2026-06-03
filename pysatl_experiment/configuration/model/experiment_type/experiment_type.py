"""Experiment type definitions."""

from enum import Enum
from typing import cast


class ExperimentType(str, Enum):
    """Supported experiment types."""

    CRITICAL_VALUE = "critical_value"
    POWER = "power"
    TIME_COMPLEXITY = "time_complexity"

    @classmethod
    def list(cls) -> list[str]:
        """
        Return all enum values.

        Returns
        -------
        list[str]
            Available enum values.
        """
        return [cast(ExperimentType, member).value for member in cls]  # TODO: check in tests
