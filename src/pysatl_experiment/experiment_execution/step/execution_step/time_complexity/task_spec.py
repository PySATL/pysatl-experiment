"""Prepared inputs for one time complexity computation."""

from dataclasses import dataclass

from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.types import SampleSetSpec


@dataclass(frozen=True, slots=True)
class TimeComplexityTask:
    """Measure one criterion on one distribution and sample size."""

    criterion: CriterionSpec
    sample_set: SampleSetSpec
