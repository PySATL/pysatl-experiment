"""Critical value experiment schema."""

from typing import Literal

from .execution import ExecutionSchema
from .experiment import ExperimentSchema
from .generation import SampleGenerationSchema


class CriticalValueSchema(ExperimentSchema):
    """Critical value experiment input."""

    experiment_type: Literal["critical_value"]
    generate: SampleGenerationSchema
    execute: ExecutionSchema
