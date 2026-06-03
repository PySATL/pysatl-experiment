"""Criterion model."""

from dataclasses import dataclass


@dataclass
class Criterion:
    """
    Goodness-of-fit criterion definition.

    Attributes
    ----------
    criterion_code : str
        Short criterion identifier (e.g. ``"KS"`` or ``"AD"``).
    parameters : list[float]
        Criterion-specific numeric parameters.
    """

    criterion_code: str
    parameters: list[float]
