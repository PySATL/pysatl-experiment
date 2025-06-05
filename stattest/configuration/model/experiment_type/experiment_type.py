from enum import Enum


class ExperimentType(Enum):
    """
    Experiment type.
    """

    CRITICAL_VALUE = "critical_value"
    POWER = "power"
    TIME_COMPLEXITY = "time_complexity"
