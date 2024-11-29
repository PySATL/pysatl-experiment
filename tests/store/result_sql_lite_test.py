from pathlib import Path

import numpy as np
import pytest

from stattest.experiment.configuration import TestWorkerResult
from stattest.persistence.sql_lite_store import ResultSqLiteStore


store_name = "pysatl.sqlite"


class TestResult(TestWorkerResult):
    def __init__(self, name, values):
        self.name = name
        self.values = values


class TestBenchmarkResultSqLiteStoreService:
    @pytest.fixture
    def store(self):
        store = ResultSqLiteStore(name=store_name)
        store.init()
        return store

    def teardown_method(self):
        try:
            Path(store_name).unlink()
            Path(store_name + "-journal").unlink()
        except OSError:
            pass

    def test_get_results_empty(self, store):
        assert len(store.get_results(0, 5)) == 0

    def test_get_result_empty(self, store):
        assert store.get_result("test") is None

    def test_get_result_value(self, store):
        store.insert_result("test", TestResult("name", [0.1, 0.5]))
        result = store.get_result("test")
        assert result.name == "name"
        assert np.array_equal(result.values, [0.1, 0.5])

    def test_get_results_value(self, store):
        store.insert_result("test", TestResult("name1", [0.1, 0.5]))
        store.insert_result("test1", TestResult("name", [0.3, 0.2]))
        result = store.get_results(0, 5)
        result = sorted(list(map(lambda x: x.name, result)))
        assert result[0] == "name"
        assert result[1] == "name1"
