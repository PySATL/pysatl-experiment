from dataclasses import dataclass


@dataclass
class Criterion:
    """
    Criterion configuration (criterion code + parameters).
    """
    criterion_code: str
    parameters: list[float]
