"""Structured identity of one curve in a time complexity report."""

import json
from dataclasses import dataclass

from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel, TimeComplexityQuery


@dataclass(frozen=True, slots=True, order=True)
class TimeComplexityReportSeries:
    """Distinguish source, criterion parameters and repetition count across sizes."""

    criterion_code: str
    criterion_parameters: tuple[tuple[str, float], ...]
    generator_code: str
    samples_count: int

    @classmethod
    def from_result(cls, result: TimeComplexityModel | TimeComplexityQuery) -> "TimeComplexityReportSeries":
        """Normalize parameter order and numeric spelling for matching and grouping."""
        return cls(
            criterion_code=result.criterion_code,
            criterion_parameters=tuple(
                sorted((name, float(value)) for name, value in result.criterion_parameters.items())
            ),
            generator_code=result.generator_code,
            samples_count=result.samples_count,
        )

    @property
    def label(self) -> str:
        """Describe the series for the table and chart without using labels as keys."""
        parameters = json.dumps(dict(self.criterion_parameters), sort_keys=True, ensure_ascii=False)
        return f"{self.criterion_code} {parameters} ({self.generator_code}; repeats={self.samples_count})"
