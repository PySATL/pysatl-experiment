"""Common criterion and execution schemas."""

from typing import Annotated, Literal

from pydantic import Field, field_validator
from pysatl_criterion import DistributionType

from pysatl_experiment.types import StepType

from .base import ConfigSchema, Number, PositiveInt, Probability


class CriterionSchema(ConfigSchema):
    """Criterion short code and named numeric parameters."""

    criterion_code: str = Field(min_length=1)
    parameters: dict[str, Number] = Field(default_factory=dict)

    @field_validator("criterion_code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        """Normalize only after Pydantic has verified the string type."""
        return value.upper()


class ExecutionSchema(ConfigSchema):
    """Settings for processing generated samples."""

    hypothesis: DistributionType
    hypothesis_params: dict[str, Number]
    criteria: list[CriterionSchema] = Field(min_length=1)
    executor_type: Literal[StepType.STANDARD]
    monte_carlo_count: Annotated[int, Field(strict=True, ge=100)]
    parallel_workers: PositiveInt = 1
    write_batch_size: PositiveInt = 20
    significance_levels: list[Probability] = Field(min_length=1)

    @field_validator("executor_type", mode="before")
    @classmethod
    def parse_executor_type(cls, value):
        """Accept the JSON string for the supported implementation."""
        return StepType.STANDARD if value == "standard" else value
