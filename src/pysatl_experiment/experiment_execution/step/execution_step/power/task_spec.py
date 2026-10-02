"""Prepared inputs for one power computation."""

from dataclasses import dataclass

from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.types import SampleSetSpec


@dataclass(frozen=True, slots=True)
class PowerTask:
    """Describe the criterion and sample set without live dependencies."""

    criterion: CriterionSpec
    sample_set: SampleSetSpec

    significance_level: float
    alternative_parameters: dict[str, float | list[float]]
