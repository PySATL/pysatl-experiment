from dataclasses import dataclass


@dataclass
class Alternative:
    """
    Alternative configuration (generator code + parameters).
    """

    generator_name: str
    parameters: list[float]
