from enum import Enum


class ExperimentType(str, Enum):
    """
    Experiment type.
    """

    CRITICAL_VALUE = "critical_value"
    POWER = "power"
    TIME_COMPLEXITY = "time_complexity"

    @classmethod
    def list(cls) -> list[str]:
        """
        Collect all enum values.

        @return: enum values
        """
        return [member.value for member in cls]
