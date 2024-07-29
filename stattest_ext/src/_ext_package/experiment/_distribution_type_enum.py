import enum


@enum.unique
class Distribution(enum.Enum):
    """
    Enum class for representing distribution types.
    """
    no_type = "no_type"
    normal = "normal"
    exponential = "exponential"
