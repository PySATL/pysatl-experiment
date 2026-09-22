"""Context objects for time complexity report generation."""

from dataclasses import dataclass
from pathlib import Path

from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic

from pysatl_experiment.configuration.criteria_config import CriterionConfig
from pysatl_experiment.configuration.models.report_mode import ReportMode


@dataclass
class TimeComplexityReportData:
    """Single criterion and sample-size pair used by report collection."""

    criterion: AbstractGoodnessOfFitStatistic
    sample_size: int


@dataclass
class TimeComplexityReportStepContext:
    """Configuration for a time complexity report-building step."""

    experiment_name: str
    report_name: str
    criteria_config: list[CriterionConfig]
    sample_sizes: list[int]
    monte_carlo_count: int
    samples_count: int
    results_path: Path
    report_mode: ReportMode
    data_list: list[TimeComplexityReportData]
