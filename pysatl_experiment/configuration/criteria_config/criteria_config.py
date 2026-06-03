"""Criterion configuration model."""

from dataclasses import dataclass

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from pysatl_experiment.configuration.model.criterion.criterion import Criterion


@dataclass
class CriterionConfig:  # TODO: move to model?? + check description with original Criterion (only GoF?)
    """
    Configuration for a goodness-of-fit criterion.

    Attributes
    ----------
    criterion : Criterion
        Selected criterion metadata.
    criterion_code : str
        Full criterion code.
    statistics_class_object : AbstractGoodnessOfFitStatistic
        Criterion implementation instance.
    """

    criterion: Criterion
    criterion_code: str
    statistics_class_object: AbstractGoodnessOfFitStatistic
