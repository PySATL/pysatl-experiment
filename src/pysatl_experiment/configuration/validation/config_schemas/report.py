"""Report output settings and path validation."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator

from pysatl_experiment.constants import RESULTS_DIR, USER_DATA_DIR
from pysatl_experiment.types import ReportMode, StepType

from .base import ConfigSchema


class ReportSchema(ConfigSchema):
    """Report implementation and output mode."""

    report_builder_type: Literal[StepType.STANDARD]
    report_mode: ReportMode
    results_path: Path = Field(default_factory=lambda: Path(USER_DATA_DIR) / RESULTS_DIR, validate_default=True)

    @field_validator("results_path", mode="before")
    @classmethod
    def nonempty_results_path(cls, value):
        """Reject empty strings and null bytes before converting to Path."""
        if isinstance(value, str) and (not value.strip() or "\x00" in value):
            raise ValueError("results_path must be a nonempty path without null bytes")
        return value

    @field_validator("results_path")
    @classmethod
    def resolve_results_path(cls, value: Path) -> Path:
        """Resolve relative paths against the working directory without creating them."""
        return value.expanduser().resolve()

    @field_validator("report_builder_type", mode="before")
    @classmethod
    def parse_report_type(cls, value):
        """Accept the JSON string for the supported implementation."""
        return StepType.STANDARD if value == "standard" else value
