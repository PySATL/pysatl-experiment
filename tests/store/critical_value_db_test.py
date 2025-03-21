from pathlib import Path

import numpy as np
import pytest

from pysatl_experiment.persistence.db_store import CriticalValueDbStore


store_name = "pysatl.sqlite"


class TestCriticalValueSqLiteStoreService:
    @pytest.fixture
    def store(self):
        store = CriticalValueDbStore(db_url="sqlite:///" + store_name)
        store.init()
        return store

    def teardown_method(self, method):
        try:
            Path(store_name).unlink()
            Path(store_name + "-journal").unlink()
        except OSError:
            pass

    def test_get_critical_value_empty(self, store):
        assert store.get_critical_value("", 5, 0.05) is None

    def test_get_distribution_empty(self, store):
        assert store.get_distribution("", 5) is None

    def test_get_critical_value(self, store):
        store.insert_critical_value("test", 2, 0.05, 1.5)
        value = store.get_critical_value("test", 2, 0.05)
        assert value == 1.5

    def test_get_distribution(self, store):
        store.insert_distribution("gen_code1", 4, [0.1, 0.2, 0.3, 0.4])
        ar = np.array(store.get_distribution("gen_code1", 4))
        expected = np.array([0.1, 0.2, 0.3, 0.4])
        assert np.array_equal(ar, expected)
