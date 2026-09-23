"""Experiment generation configuration models."""

from dataclasses import dataclass

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.step_type import StepType


@dataclass
class GenerationConfig:
    """Configuration for sample generation.

    Parameters
    ----------
    samples_count : int
        Number of samples to generate.
    generator_type : StepType
        Type of generator used to generate samples.
    distribution_type : DistributionType
        Probability distribution used for sample generation.
    distribution_params : dict[str, float]
        Parameters of the probability distribution.
    sample_sizes : list[int]
        Sample sizes used in the experiment.
    parallel_workers : int
        Number of workers available for parallel generation.
    """

    samples_count: int
    generator_type: StepType
    distribution_type: DistributionType
    distribution_params: dict[str, float]
    sample_sizes: list[int]
    parallel_workers: int
