"""Shared experiment root settings and validation."""

from pydantic import Field, field_validator
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from pysatl_experiment.types import RunMode

from .base import ConfigSchema
from .report import ReportSchema


class ExperimentSchema(ConfigSchema):
    """Shared root settings; specialized schemas supply step structure."""

    experiment_name: str = Field(min_length=1)
    storage_connection: str = Field(min_length=1)
    run_mode: RunMode
    report: ReportSchema

    @field_validator("experiment_name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        """Preserve the existing filename restrictions."""
        if value.endswith(".json"):
            value = value[:-5]
        reserved = {"CON", "AUX", "PRN", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
        if not value or value.upper() in reserved or any(c in '\\/:*?<>|\x00"' or c.isspace() for c in value):
            raise ValueError("Invalid experiment name")
        return value

    @field_validator("storage_connection")
    @classmethod
    def valid_connection(cls, value: str) -> str:
        """Validate URL syntax without connecting to the database."""
        try:
            make_url(value)
        except ArgumentError as error:
            raise ValueError("Invalid storage connection URL") from error
        return value
