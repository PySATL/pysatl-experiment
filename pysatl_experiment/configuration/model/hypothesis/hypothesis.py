from enum import Enum


class Hypothesis(Enum):
    """
    Hypothesis.
    """

    NORMAL = "normal"
    EXPONENTIAL = "exponential"
    WEIBULL = "weibull"

    @classmethod
    def list(cls):
        """
        Collect all enum values.

        @return: enum values
        """
        return [member.value for member in cls]
