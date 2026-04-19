from dataclasses import dataclass


@dataclass
class HypothesisGeneratorData:
    """
    Data for hypothesis generator.
    """

    generator_name: str
    parameters: list[float]
