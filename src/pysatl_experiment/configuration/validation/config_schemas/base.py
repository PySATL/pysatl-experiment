"""Shared schema settings and constrained numeric types."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


PositiveInt = Annotated[int, Field(strict=True, gt=0)]
SampleSize = Annotated[int, Field(strict=True, ge=10)]
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Probability = Annotated[float, Field(strict=True, gt=0, lt=1, allow_inf_nan=False)]
ParameterRange = Annotated[list[Number], Field(min_length=2, max_length=2)]


class ConfigSchema(BaseModel):
    """Reject unknown fields and implicit conversions of string fields."""

    model_config = ConfigDict(extra="forbid")
