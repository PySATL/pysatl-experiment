import os

import pytest

from stattest.core.store import JsonStoreService

filename = 'cache.json'


class TestJsonStoreService:

    @pytest.fixture
    def store(self):
        return JsonStoreService(filename=filename)

    def teardown_method(self, method):
        try:
            os.remove(filename)
        except OSError:
            pass

    def test_get_empty(self, store):
        assert store.get('a') is None

    def test_get_with_level_empty(self, store):
        assert store.get_with_level(['a', 'b', 'c']) is None

    def test_put(self, store):
        store.put('a', 1)
        assert store.get('a') == 1

    def test_put_with_level(self, store):
        store.put_with_level(['a', 'b'], 2)
        assert store.get_with_level(['a', 'b']) == 2
