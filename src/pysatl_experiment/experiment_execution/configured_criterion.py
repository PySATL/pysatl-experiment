"""A criterion resolved from configuration into a runtime statistic."""

from dataclasses import dataclass

from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic

from pysatl_experiment.configuration import CriterionConfig


@dataclass
class ConfiguredCriterion:
    """
    A goodness-of-fit criterion instantiated for experiment execution.

    Attributes
    ----------
    criterion : CriterionConfig
        Selected criterion metadata.
    criterion_code : str
        Full criterion code.
    statistics_class_object : AbstractGoodnessOfFitStatistic
        Criterion implementation instance.
    """

    criterion: CriterionConfig
    criterion_code: str
    statistics_class_object: AbstractGoodnessOfFitStatistic
