from dataclasses import dataclass

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.step_type import StepType

@dataclass
class GenerationConfig:
    samples_count: int
    generator_type: StepType
    distribution_type: DistributionType
    distribution_params: dict[str, float]
    sample_sizes: list[int]
    parallel_workers: int