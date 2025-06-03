from dataclasses import dataclass

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic


@dataclass
class ExecutionStepData:
    """
    Data for execution step.
    """

    criterion: AbstractGoodnessOfFitStatistic
    sample_size: int
