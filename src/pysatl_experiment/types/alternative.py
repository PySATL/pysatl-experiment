"""Alternative distribution model."""

from dataclasses import dataclass


@dataclass
class Alternative:
    """
    Alternative distribution configuration.

    Attributes
    ----------
    distribution_type : str
        Alternative distribution generator identifier.
    parameters : dict[str, float | list[float]]
        Generator-specific parameters, including configured ranges.
    """

    distribution_type: str
    parameters: dict[str, float | list[float]]
