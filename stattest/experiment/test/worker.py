from typing_extensions import override

from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.experiment.configuration.configuration import TestWorker, TestWorkerResult
from stattest.experiment.test.power_calculation import calculate_test_power
from stattest.persistence.models import IPowerResultStore, ICriticalValueStore
from stattest.test import AbstractTestStatistic


class PowerWorkerResult(TestWorkerResult):
    def __init__(self, test_code, alternative_code, size, alpha, power):
        self.test_code = test_code
        self.alpha = alpha
        self.size = size
        self.power = power
        self.alternative_code = alternative_code


class PowerCalculationWorker(TestWorker):
    def __init__(self, alpha, monte_carlo_count, worker_result_store: IPowerResultStore,
                 critical_value_store: ICriticalValueStore, hypothesis: AbstractHypothesis):
        self.alpha = alpha
        self.monte_carlo_count = monte_carlo_count
        self.worker_result_store = worker_result_store
        self.critical_value_store = critical_value_store
        self.hypothesis = hypothesis

    @override
    def execute(self, test: AbstractTestStatistic, data: [[float]], code: str, size: int) -> PowerWorkerResult:

        # 1. Check power result
        power = self.worker_result_store.get_power(self.alpha, size, test.code(), code)
        if power is not None:
            return PowerWorkerResult(test.code(), code, size, self.alpha, power)

        # 2. Calculate power
        power = calculate_test_power(test, data, self.hypothesis, self.alpha, self.critical_value_store,
                                     self.monte_carlo_count)

        # 3. Save result
        self.worker_result_store.insert_power(self.alpha, size, test.code(), code, power)

        return PowerWorkerResult(test.code(), code, size, self.alpha, power)

    @override
    def save_result(self, result: PowerWorkerResult):
        pass
