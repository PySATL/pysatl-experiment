"""Alternative distribution model."""

from dataclasses import dataclass


@dataclass
class Alternative:  # TODO: check??
    """
    Alternative distribution configuration.

    Attributes
    ----------
    generator_name : str
        Alternative distribution generator identifier.
    parameters : list[float]
        Generator-specific numeric parameters.
    """

    generator_name: str
    parameters: list[float]
