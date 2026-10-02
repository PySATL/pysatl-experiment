"""Distribution and sample generation schemas."""

from typing import Literal

from pydantic import Field, field_validator
from pysatl_criterion import DistributionType

from pysatl_experiment.types import StepType

from .base import ConfigSchema, Number, ParameterRange, PositiveInt, SampleSize


class DistributionSchema(ConfigSchema):
    """Named distribution parameters, including bounded random parameters."""

    distribution_type: DistributionType
    distribution_params: dict[str, Number | ParameterRange]

    @field_validator("distribution_params")
    @classmethod
    def ordered_ranges(cls, value):
        """Require an ascending interval for each random parameter."""
        for name, parameter in value.items():
            if isinstance(parameter, list) and parameter[0] > parameter[1]:
                raise ValueError(f"{name}: range lower bound must not exceed upper bound")
        return value


class GenerationSchema(ConfigSchema):
    """Common generation settings."""

    generator_type: Literal[StepType.STANDARD]
    parallel_workers: PositiveInt = 1
    distributions: list[DistributionSchema] = Field(min_length=1)

    @field_validator("generator_type", mode="before")
    @classmethod
    def parse_generator_type(cls, value):
        """Accept the JSON string for the supported implementation."""
        return StepType.STANDARD if value == "standard" else value


class SampleGenerationSchema(GenerationSchema):
    """Generation with explicit sample sizes and number of samples."""

    samples_count: PositiveInt
    sample_sizes: list[SampleSize] = Field(min_length=1)
