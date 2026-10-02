"""Power experiment and specialized execution schemas."""

from typing import Literal

from pydantic import Field

from .base import SampleSize
from .execution import ExecutionSchema
from .experiment import ExperimentSchema
from .generation import GenerationSchema


class PowerExecutionSchema(ExecutionSchema):
    """Power execution controls the sample sizes used during generation."""

    sample_sizes: list[SampleSize] = Field(min_length=1)


class PowerSchema(ExperimentSchema):
    """Power experiment input."""

    experiment_type: Literal["power"]
    generate: GenerationSchema
    execute: PowerExecutionSchema
