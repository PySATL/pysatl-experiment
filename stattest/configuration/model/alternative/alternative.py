from dataclasses import dataclass


@dataclass
class Alternative:
    """
    Alternative configuration (generator code + parameters).
    """

    generator_code: str
    parameters: list[float]
