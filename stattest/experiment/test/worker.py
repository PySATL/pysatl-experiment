import time

import numpy as np
from pysatl.criterion import AbstractStatistic
from typing_extensions import override

from stattest.experiment.configuration.configuration import TestWorker, TestWorkerResult
from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.experiment.test.power_calculation import calculate_test_power
from stattest.parsable import Parsable
from stattest.persistence.models import ICriticalValueStore


class PowerWorkerResult(TestWorkerResult):
    def __init__(self, test_code, alternative_code, size, alpha, power):
        self.test_code = test_code
        self.alpha = alpha
        self.size = size
        self.power = power
        self.alternative_code = alternative_code


class BenchmarkWorkerResult(TestWorkerResult):
    def __init__(self, size: int, test_code: str, mean: float, median: float, std: float):
        self.size = size
        self.mean = mean
        self.median = median
        self.std = std
        self.test_code = test_code


class BenchmarkWorker(TestWorker, Parsable):
    def __init__(self):
        super().__init__()

    def build_id(
        self, test: AbstractStatistic, data: list[list[float]], code: str, size: int
    ) -> str:
        return "_".join(["benchmark", str(size), test.code(), code])

    @override
    def execute(
        self, test: AbstractStatistic, data: list[list[float]], code: str, size: int
    ) -> BenchmarkWorkerResult:
        result = []
        for rvs in data:
            t1 = time.time()
            test.execute_statistic(rvs)
            t2 = time.time()
            result.append((t2 - t1) * 1000)

        mean = float(np.mean(result))
        median = float(np.median(result))
        std = float(np.std(result))
        return BenchmarkWorkerResult(size, test.code(), mean, median, std)


class PowerCalculationWorker(TestWorker, Parsable):
    def __init__(
        self,
        alpha: float,
        monte_carlo_count: int,
        cv_store: ICriticalValueStore,
        hypothesis: AbstractHypothesis,
    ):
        self.alpha = alpha
        self.monte_carlo_count = monte_carlo_count
        self.cv_store = cv_store
        self.hypothesis = hypothesis

    @override
    def init(self):
        self.cv_store.init()

    def build_id(
        self, test: AbstractStatistic, data: list[list[float]], code: str, size: int
    ) -> str:
        return "_".join([str(self.alpha), str(size), test.code(), code])

    @override
    def execute(
        self, test: AbstractStatistic, data: list[list[float]], code: str, size: int
    ) -> PowerWorkerResult:
        power = calculate_test_power(
            test, data, self.hypothesis, self.alpha, self.cv_store, self.monte_carlo_count
        )
        return PowerWorkerResult(test.code(), code, size, self.alpha, power)
