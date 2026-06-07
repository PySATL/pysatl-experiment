"""Statistical hypothesis definitions."""

from enum import Enum


class Hypothesis(Enum):
    """Supported goodness-of-fit hypotheses."""

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
        Return all enum values.

        Returns
        -------
        list[str]
            Available enum values.
        """
        return [member.value for member in cls]
