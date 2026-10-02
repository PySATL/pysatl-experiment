"""Time complexity experiment schema."""

from typing import Literal

from .execution import ExecutionSchema
from .experiment import ExperimentSchema
from .generation import SampleGenerationSchema


class TimeComplexitySchema(ExperimentSchema):
    """Time complexity experiment input."""

    experiment_type: Literal["time_complexity"]
    generate: SampleGenerationSchema
    execute: ExecutionSchema
