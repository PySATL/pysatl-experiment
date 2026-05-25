from enum import Enum


class Hypothesis(Enum):
    """
    Hypothesis.
    """

    NORMAL = "normal"
    EXPONENTIAL = "exponential"
    WEIBULL = "weibull"
    GAMMA = "gamma"
    BETA = "beta"
    LOGNORMAL = "lognormal"
    STUDENT = "student"
    UNIFORM = "uniform"

    @classmethod
    def list(cls):
        """
        Collect all enum values.

        @return: enum values
        """
        return [member.value for member in cls]
