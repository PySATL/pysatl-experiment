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
    parameters : dict[str, float]
        Generator-specific numeric parameters.
    """

    parameters: dict[str, float]
    distribution_type: DistributionType

    @property
    def distribution_type(self) -> DistributionType:
        """Return generator code using the newer naming convention."""
        return self.distribution_type
