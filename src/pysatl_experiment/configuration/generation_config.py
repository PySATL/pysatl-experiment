from dataclasses import dataclass

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.experiment_raw_config import GenerationDistributionRawConfig, GenerationRawConfig
from pysatl_experiment.configuration.models.step_type import StepType


@dataclass
class GenerationDistributionConfig:
    distribution_type: DistributionType
    distribution_params: dict[str, float | list[float]]

    @staticmethod
    def from_row_config(conf: GenerationDistributionRawConfig) -> None:
        return GenerationDistributionConfig(
            distribution_type=DistributionType(conf.distribution_type), distribution_params=conf.distribution_params
        )


@dataclass
class GenerationConfig:
    samples_count: int
    generator_type: StepType
    distributions: list[GenerationDistributionConfig]
    sample_sizes: list[int]
    parallel_workers: int

    @staticmethod
    def from_row_config(conf: GenerationRawConfig) -> None:
        return GenerationConfig(
            samples_count=conf.samples_count,
            generator_type=StepType(conf.generator_type),
            distributions=[GenerationDistributionConfig.from_row_config(e) for e in conf.distributions],
            sample_sizes=conf.sample_sizes,
            parallel_workers=conf.parallel_workers,
        )
