"""Data containers for random sample generation steps."""

from dataclasses import dataclass

from pysatl_criterion.generator.model import AbstractRVSGenerator


@dataclass
class GenerationData:
    """
    Configuration for random sample generation.

    Attributes
    ----------
    generator : AbstractRVSGenerator
        Generator instance.
    sample_size : int
        Size of generated samples.
    samples_count : int
        Number of samples to generate.
    """

    generator: AbstractRVSGenerator
    sample_size: int
    samples_count: int

@dataclass
class GenerationStepContext:
    """
    Configuration for random sample generation.

    Attributes
    ----------
    data_list : list[GenerationData]
    experiment_name : str
    """

    data_list: list[GenerationData]
    experiment_name: str
