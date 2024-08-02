import enum


@enum.unique
class Hypothesis(enum.Enum):
    """
    Enum class for representing hypotheses.
    """
    h0 = 0
    h1 = 1
