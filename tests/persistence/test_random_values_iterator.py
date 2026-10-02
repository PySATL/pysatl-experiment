"""Traversal, buffering and limits belong to the iterator rather than the DAO."""

from unittest.mock import Mock, call

import pytest

from pysatl_experiment.persistence.models.random_values import RandomValuesBatch, RandomValuesFilter, RandomValuesModel
from pysatl_experiment.persistence.random_values_iterator import RandomValuesIterator


def samples(count):
    return [RandomValuesModel("experiment", "generator", {}, 1, [float(i)]) for i in range(count)]


def test_iterator_is_lazy_and_refills_only_when_current_page_is_consumed():
    store = Mock()
    query = RandomValuesFilter(experiment_name="experiment")
    rows = samples(5)
    store.read_bulk.side_effect = [RandomValuesBatch(rows[:3], 3), RandomValuesBatch(rows[3:], None)]
    iterator = RandomValuesIterator(store, query, batch_size=3)
    assert iter(iterator) is iterator
    store.read_bulk.assert_not_called()
    assert next(iterator) == rows[0]
    assert next(iterator) == rows[1]
    assert store.read_bulk.call_count == 1
    assert list(iterator) == rows[2:]
    assert store.read_bulk.call_args_list == [
        call(query, after_id=None, batch_size=3),
        call(query, after_id=3, batch_size=3),
    ]
    assert list(iterator) == []
    assert store.read_bulk.call_count == 2


def test_limit_trims_last_request_and_avoids_extra_reads():
    store = Mock()
    query = RandomValuesFilter(experiment_name="experiment")
    rows = samples(5)
    store.read_bulk.side_effect = [RandomValuesBatch(rows[:3], 3), RandomValuesBatch(rows[3:], 5)]
    iterator = RandomValuesIterator(store, query, batch_size=3, limit=5)
    assert list(iterator) == rows
    assert store.read_bulk.call_args_list == [
        call(query, after_id=None, batch_size=3),
        call(query, after_id=3, batch_size=2),
    ]
    assert list(iterator) == []


def test_zero_limit_never_calls_storage():
    store = Mock()
    assert list(RandomValuesIterator(store, RandomValuesFilter(experiment_name="experiment"), limit=0)) == []
    store.read_bulk.assert_not_called()


def test_empty_page_ends_iteration_even_with_a_larger_limit():
    store = Mock()
    store.read_bulk.return_value = RandomValuesBatch([], None)
    iterator = RandomValuesIterator(store, RandomValuesFilter(experiment_name="experiment"), limit=5)
    assert list(iterator) == []
    assert list(iterator) == []
    assert store.read_bulk.call_count == 1


@pytest.mark.parametrize("limit", [-1, True, 2.5])
def test_invalid_limit(limit):
    with pytest.raises(ValueError, match="limit"):
        RandomValuesIterator(Mock(), RandomValuesFilter(experiment_name="experiment"), limit=limit)


@pytest.mark.parametrize("size", [0, -1, True, 2.5])
def test_invalid_batch_size(size):
    with pytest.raises(ValueError, match="batch_size"):
        RandomValuesIterator(Mock(), RandomValuesFilter(experiment_name="experiment"), batch_size=size)
