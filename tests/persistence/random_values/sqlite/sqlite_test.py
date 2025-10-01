from __future__ import annotations

from pathlib import Path

import pytest

from pysatl_experiment.persistence.model.random_values.random_values import (
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)
from pysatl_experiment.persistence.random_values.sqlite.sqlite import SQLiteRandomValuesStorage


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "rvs.sqlite"


@pytest.fixture()
def storage(db_path: Path) -> SQLiteRandomValuesStorage:
    store = SQLiteRandomValuesStorage(str(db_path))
    store.init()
    return store


def test_guard_requires_init(db_path: Path) -> None:
    store = SQLiteRandomValuesStorage(str(db_path))
    with pytest.raises(RuntimeError):
        _ = store.get_data(
            RandomValuesQuery(
                generator_name="gen",
                generator_parameters=[0.5],
                sample_size=10,
                sample_num=1,
            )
        )


def test_get_data_empty_returns_none(storage: SQLiteRandomValuesStorage) -> None:
    query = RandomValuesQuery(
        generator_name="gen_A",
        generator_parameters=[0.1, 0.2],
        sample_size=20,
        sample_num=1,
    )
    assert storage.get_data(query) is None


def test_insert_and_get_single_sample(storage: SQLiteRandomValuesStorage) -> None:
    model = RandomValuesModel(
        generator_name="gen_A",
        generator_parameters=[0.1, 0.2],
        sample_size=20,
        sample_num=1,
        data=[0.11, 0.22, 0.33],
    )
    storage.insert_data(model)

    got = storage.get_data(
        RandomValuesQuery(
            generator_name="gen_A",
            generator_parameters=[0.1, 0.2],
            sample_size=20,
            sample_num=1,
        )
    )

    assert got is not None
    assert got.generator_name == model.generator_name
    assert got.generator_parameters == model.generator_parameters
    assert got.sample_size == model.sample_size
    assert got.sample_num == model.sample_num
    assert got.data == model.data


def test_delete_single_sample(storage: SQLiteRandomValuesStorage) -> None:
    model = RandomValuesModel(
        generator_name="gen_B",
        generator_parameters=[0.3],
        sample_size=5,
        sample_num=2,
        data=[1.0, 2.0],
    )
    storage.insert_data(model)

    storage.delete_data(
        RandomValuesQuery(
            generator_name="gen_B",
            generator_parameters=[0.3],
            sample_size=5,
            sample_num=2,
        )
    )

    assert (
        storage.get_data(
            RandomValuesQuery(
                generator_name="gen_B",
                generator_parameters=[0.3],
                sample_size=5,
                sample_num=2,
            )
        )
        is None
    )


def test_insert_all_and_get_all_and_count(storage: SQLiteRandomValuesStorage) -> None:
    all_model = RandomValuesAllModel(
        generator_name="gen_C",
        generator_parameters=[0.7, 0.9],
        sample_size=4,
        data=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
    )
    storage.insert_all_data(all_model)

    count = storage.get_rvs_count(
        RandomValuesAllQuery(
            generator_name="gen_C",
            generator_parameters=[0.7, 0.9],
            sample_size=4,
        )
    )
    assert count == 3

    all_data = storage.get_all_data(
        RandomValuesAllQuery(
            generator_name="gen_C",
            generator_parameters=[0.7, 0.9],
            sample_size=4,
        )
    )

    assert isinstance(all_data, list)
    assert [m.sample_num for m in all_data] == [1, 2, 3]
    assert [m.data for m in all_data] == [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]


def test_get_count_data_limits(storage: SQLiteRandomValuesStorage) -> None:
    all_model = RandomValuesAllModel(
        generator_name="gen_D",
        generator_parameters=[1.1],
        sample_size=3,
        data=[[1], [2], [3], [4]],
    )
    storage.insert_all_data(all_model)

    limited = storage.get_count_data(
        RandomValuesCountQuery(
            generator_name="gen_D",
            generator_parameters=[1.1],
            sample_size=3,
            count=2,
        )
    )

    assert [m.sample_num for m in limited] == [1, 2]
    assert [m.data for m in limited] == [[1], [2]]


def test_delete_all_data(storage: SQLiteRandomValuesStorage) -> None:
    all_model = RandomValuesAllModel(
        generator_name="gen_E",
        generator_parameters=[2.2],
        sample_size=8,
        data=[[10, 20], [30, 40]],
    )
    storage.insert_all_data(all_model)

    storage.delete_all_data(
        RandomValuesAllQuery(
            generator_name="gen_E",
            generator_parameters=[2.2],
            sample_size=8,
        )
    )

    count_after = storage.get_rvs_count(
        RandomValuesAllQuery(
            generator_name="gen_E",
            generator_parameters=[2.2],
            sample_size=8,
        )
    )
    assert count_after == 0

    all_data_after = storage.get_all_data(
        RandomValuesAllQuery(
            generator_name="gen_E",
            generator_parameters=[2.2],
            sample_size=8,
        )
    )
    assert all_data_after == []
