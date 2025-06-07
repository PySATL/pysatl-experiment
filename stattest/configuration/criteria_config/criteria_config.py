from dataclasses import dataclass

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from stattest.configuration.model.criterion.criterion import Criterion


@dataclass
class CriterionConfig:
    """
    Criteria configuration.
    """
    criterion: Criterion
    criterion_code: str
    statistics_class_object: AbstractGoodnessOfFitStatistic
