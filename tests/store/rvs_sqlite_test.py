import os

import numpy as np
import pytest

from stattest.persistence.sql_lite_store import RvsSqLiteStore


store_name = "pysatl.sqlite"


class TestRvsSqLiteStoreService:
    @pytest.fixture
    def store(self):
        store = RvsSqLiteStore(name=store_name)
        store.init()
        return store

    def teardown_method(self, method):
        try:
            os.remove(store_name)
            os.remove(store_name + "-journal")
        except OSError:
            pass

    def test_get_rvs_stat_empty(self, store):
        assert len(store.get_rvs_stat()) is 0

    def test_get_rvs_empty(self, store):
        assert len(store.get_rvs("test", 2)) is 0

    def test_insert_rvs(self, store):
        store.insert_rvs("gen_code", 10, [0.1, 0.2])
        ar = np.array(store.get_rvs_stat())
        expected = np.array([("gen_code", 10, 1)])
        assert np.array_equal(ar, expected)

    def test_insert_all_rvs(self, store):
        store.insert_all_rvs("gen_code1", 2, [[0.1, 0.2], [0.3, 0.4]])
        ar = np.array(store.get_rvs_stat())
        expected = np.array([("gen_code1", 2, 2)])
        assert np.array_equal(ar, expected)

    def test_get_rvs(self, store):
        store.insert_all_rvs("gen_code2", 2, [[0.1, 0.2], [0.3, 0.4]])
        ar = np.array(store.get_rvs("gen_code2", 2))
        expected = np.array([[0.1, 0.2], [0.3, 0.4]])
        assert np.array_equal(ar, expected)

    def test_clear_rvs(self, store):
        store.insert_all_rvs("gen_code2", 2, [[0.1, 0.2], [0.3, 0.4]])
        store.clear_all_rvs()
        assert len(store.get_rvs("gen_code2", 2)) is 0
