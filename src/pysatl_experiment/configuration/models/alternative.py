"""Alternative distribution model."""

from dataclasses import dataclass

from pysatl_criterion import DistributionType


@dataclass
class Alternative:
    """
    Alternative distribution configuration.

    Attributes
    ----------
    distribution_type : str
        Alternative distribution generator identifier.
    parameters : list[float]
        Generator-specific numeric parameters.
    """

    distribution_type: DistributionType
    parameters: list[float]
