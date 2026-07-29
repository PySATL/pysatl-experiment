"""Data containers for random sample generation steps."""

from dataclasses import dataclass

from pysatl_criterion.generator.model import AbstractRVSGenerator


@dataclass
class GenerationStepData:
    """
    Configuration for random sample generation.

    Attributes
    ----------
    generator : AbstractRVSGenerator
        Generator instance.
    generator_name : str
        Generator identifier.
    generator_parameters : list[float]
        Generator parameters.
    sample_size : int
        Size of generated samples.
    count : int
        Number of samples to generate.
    """

    generator: AbstractRVSGenerator
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    count: int
