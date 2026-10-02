"""Tests for SQLAlchemy time complexity storage implementation."""

from __future__ import annotations

from pathlib import Path

import pytest

from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel, TimeComplexityQuery
from pysatl_experiment.persistence.sqlalchemy.time_complexity import AlchemyTimeComplexityStorage


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "time_complexity.sqlite"


@pytest.fixture()
def storage(db_path: Path) -> AlchemyTimeComplexityStorage:
    store = AlchemyTimeComplexityStorage(db_url="sqlite:///:memory:")
    store.init()
    return store


def test_guard_requires_init(db_path: Path) -> None:
    store = AlchemyTimeComplexityStorage(str(db_path))
    with pytest.raises(RuntimeError):
        _ = store.get_data(
            TimeComplexityQuery(
                generator_code="normal",
                experiment_name="experiment-a",
                criterion_code="crit_A",
                criterion_parameters={"alpha": 0.1, "beta": 0.2},
                sample_size=10,
                samples_count=100,
            )
        )


def test_get_data_empty_returns_none(storage: AlchemyTimeComplexityStorage) -> None:
    query = TimeComplexityQuery(
        generator_code="normal",
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"alpha": 0.1, "beta": 0.2},
        sample_size=10,
        samples_count=100,
    )
    assert storage.get_data(query) is None


def test_insert_and_get(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        generator_code="normal",
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"alpha": 0.1, "beta": 0.2},
        sample_size=10,
        samples_count=100,
        results_times=[1.0, 2.0, 3.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            generator_code="normal",
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1, "beta": 0.2},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert got.experiment_name == model.experiment_name
    assert got.criterion_code == model.criterion_code
    assert got.criterion_parameters == model.criterion_parameters
    assert got.sample_size == model.sample_size
    assert got.samples_count == model.samples_count
    assert got.results_times == model.results_times


def test_bulk_insert(storage: AlchemyTimeComplexityStorage) -> None:
    models = [
        TimeComplexityModel(
            generator_code="normal",
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
            results_times=[1.0],
        ),
        TimeComplexityModel(
            generator_code="normal",
            experiment_name="experiment-b",
            criterion_code="crit_B",
            criterion_parameters={"alpha": 0.2},
            sample_size=20,
            samples_count=200,
            results_times=[2.0],
        ),
    ]

    storage.bulk_insert(models)

    for model in models:
        got = storage.get_data(
            TimeComplexityQuery(
                generator_code="normal",
                experiment_name=model.experiment_name,
                criterion_code=model.criterion_code,
                criterion_parameters=model.criterion_parameters,
                sample_size=model.sample_size,
                samples_count=model.samples_count,
            )
        )
        assert got == model


def test_bulk_insert_updates_existing_record(storage: AlchemyTimeComplexityStorage) -> None:
    storage.insert_data(
        TimeComplexityModel(
            generator_code="normal",
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
            results_times=[1.0],
        )
    )
    updated = TimeComplexityModel(
        generator_code="normal",
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"alpha": 0.1},
        sample_size=10,
        samples_count=100,
        results_times=[2.0, 3.0],
    )

    storage.bulk_insert([updated])

    got = storage.get_data(
        TimeComplexityQuery(
            generator_code="normal",
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
        )
    )
    assert got == updated


def test_get_data_filters_by_experiment_name(storage: AlchemyTimeComplexityStorage) -> None:
    storage.bulk_insert(
        [
            TimeComplexityModel(
                generator_code="normal",
                experiment_name="experiment-a",
                criterion_code="crit_A",
                criterion_parameters={"alpha": 0.1},
                sample_size=10,
                samples_count=100,
                results_times=[1.0],
            ),
            TimeComplexityModel(
                generator_code="normal",
                experiment_name="experiment-b",
                criterion_code="crit_A",
                criterion_parameters={"alpha": 0.1},
                sample_size=10,
                samples_count=100,
                results_times=[2.0],
            ),
        ]
    )

    got = storage.get_data(
        TimeComplexityQuery(
            generator_code="normal",
            experiment_name="experiment-b",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 0.1},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert got.experiment_name == "experiment-b"
    assert got.results_times == [2.0]


def test_criterion_parameters_are_order_independent(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        generator_code="normal",
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters={"zeta": 2.0, "alpha": 1.0},
        sample_size=10,
        samples_count=100,
        results_times=[1.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            generator_code="normal",
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"alpha": 1.0, "zeta": 2.0},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert list(got.criterion_parameters) == ["alpha", "zeta"]
    assert got.results_times == [1.0]


def test_criterion_parameter_lists_are_normalized_in_storage(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        generator_code="normal",
        experiment_name="experiment-a",
        criterion_code="crit_A",
        criterion_parameters=[0.1, 0.2],
        sample_size=10,
        samples_count=100,
        results_times=[1.0],
    )
    storage.insert_data(model)

    got = storage.get_data(
        TimeComplexityQuery(
            generator_code="normal",
            experiment_name="experiment-a",
            criterion_code="crit_A",
            criterion_parameters={"0": 0.1, "1": 0.2},
            sample_size=10,
            samples_count=100,
        )
    )

    assert got is not None
    assert got.criterion_parameters == {"0": 0.1, "1": 0.2}
    assert got.results_times == [1.0]


def test_delete_data(storage: AlchemyTimeComplexityStorage) -> None:
    model = TimeComplexityModel(
        generator_code="normal",
        experiment_name="experiment-b",
        criterion_code="crit_B",
        criterion_parameters={"alpha": 0.3},
        sample_size=5,
        samples_count=50,
        results_times=[0.5, 0.6],
    )
    storage.insert_data(model)

    storage.delete_data(
        TimeComplexityQuery(
            generator_code="normal",
            experiment_name="experiment-b",
            criterion_code="crit_B",
            criterion_parameters={"alpha": 0.3},
            sample_size=5,
            samples_count=50,
        )
    )

    assert (
        storage.get_data(
            TimeComplexityQuery(
                generator_code="normal",
                experiment_name="experiment-b",
                criterion_code="crit_B",
                criterion_parameters={"alpha": 0.3},
                sample_size=5,
                samples_count=50,
            )
        )
        is None
    )


def timing(index: int, experiment_name: str = "first") -> TimeComplexityModel:
    return TimeComplexityModel(experiment_name, "KS", {}, index + 1, 10, [float(index)], "normal")


def test_bulk_pages_and_iterator(storage: AlchemyTimeComplexityStorage) -> None:
    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter
    from pysatl_experiment.persistence.time_complexity_iterator import TimeComplexityIterator

    rows = [timing(i) for i in range(5)]
    storage.bulk_insert(
        (row for pair in zip(rows, [timing(i, "other") for i in range(5)], strict=True) for row in pair), batch_size=2
    )
    query = TimeComplexityFilter(experiment_name="first")
    first = storage.read_bulk(query, batch_size=2)
    second = storage.read_bulk(query, after_id=first.next_after_id, batch_size=2)
    third = storage.read_bulk(query, after_id=second.next_after_id, batch_size=2)
    assert [first.items, second.items, third.items] == [rows[:2], rows[2:4], rows[4:]]
    assert third.next_after_id is None
    assert list(TimeComplexityIterator(storage, query, batch_size=2)) == rows
    assert list(TimeComplexityIterator(storage, query, batch_size=2, limit=3)) == rows[:3]
    assert list(TimeComplexityIterator(storage, query, limit=0)) == []
    assert list(TimeComplexityIterator(storage, TimeComplexityFilter(experiment_name="absent"))) == []


def test_full_final_page_and_filters(storage: AlchemyTimeComplexityStorage) -> None:
    from dataclasses import replace

    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    row = timing(1)
    storage.bulk_insert([row, replace(row, criterion_parameters={"a": 1}), replace(row, criterion_code="AD")])
    query = TimeComplexityFilter(
        experiment_name="first", criterion_code="KS", criterion_parameters={}, sample_size=2, samples_count=10
    )
    page = storage.read_bulk(query, batch_size=1)
    assert page.items == [row]
    assert page.next_after_id is not None
    assert storage.read_bulk(query, after_id=page.next_after_id, batch_size=1).items == []
    assert storage.read_bulk(replace(query, sample_size=100)).items == []
    assert storage.read_bulk(replace(query, samples_count=100)).items == []


def test_duplicate_keys_within_and_across_batches(storage: AlchemyTimeComplexityStorage) -> None:
    from dataclasses import replace

    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    row = timing(0)
    updated = replace(row, results_times=[42.0])
    storage.bulk_insert([row, updated, row, updated], batch_size=2)
    assert storage.read_bulk(TimeComplexityFilter(experiment_name="first")).items == [updated]


def test_failed_batch_rolls_back_and_storage_remains_usable(storage: AlchemyTimeComplexityStorage) -> None:
    from dataclasses import replace

    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    rows = [timing(i) for i in range(4)]
    bad = replace(rows[3], results_times=[object()])
    with pytest.raises(TypeError):
        storage.bulk_insert([*rows[:3], bad], batch_size=2)
    query = TimeComplexityFilter(experiment_name="first")
    assert storage.read_bulk(query).items == rows[:2]
    storage.bulk_insert(rows[2:])
    assert storage.read_bulk(query).items == rows


def test_instances_use_their_own_database() -> None:
    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    first = AlchemyTimeComplexityStorage("sqlite:///:memory:")
    second = AlchemyTimeComplexityStorage("sqlite:///:memory:")
    first.init()
    first.bulk_insert([timing(0)])
    second.init()
    second.bulk_insert([timing(1)])
    first.init()
    query = TimeComplexityFilter(experiment_name="first")
    assert first.read_bulk(query).items == [timing(0)]
    assert second.read_bulk(query).items == [timing(1)]


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_bulk_rejects_invalid_bounds(storage: AlchemyTimeComplexityStorage, value) -> None:
    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    query = TimeComplexityFilter(experiment_name="first")
    with pytest.raises(ValueError):
        storage.bulk_insert([], batch_size=value)
    with pytest.raises(ValueError):
        storage.read_bulk(query, batch_size=value)
    with pytest.raises(ValueError):
        storage.read_bulk(query, after_id=value)


def test_bulk_requires_initialization() -> None:
    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    storage = AlchemyTimeComplexityStorage("sqlite:///:memory:")
    with pytest.raises(RuntimeError, match="not initialized"):
        storage.bulk_insert([])
    with pytest.raises(RuntimeError, match="not initialized"):
        storage.read_bulk(TimeComplexityFilter(experiment_name="first"))


def test_upsert_read_and_delete_are_scoped_to_source_series(storage):
    from dataclasses import asdict, replace

    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter

    first = replace(timing(0), generator_code="normal_mean_[0.0,1.0]")
    second = replace(first, generator_code="normal_mean_[0.0,2.0]", results_times=[2.0])
    storage.bulk_insert([first, second])
    updated = replace(first, results_times=[3.0])
    storage.bulk_insert([updated])
    assert storage.read_bulk(TimeComplexityFilter(experiment_name="first")).items == [updated, second]
    assert storage.read_bulk(
        TimeComplexityFilter(experiment_name="first", generator_code=second.generator_code)
    ).items == [second]
    key = asdict(first)
    key.pop("results_times")
    query = TimeComplexityQuery(**key)
    assert storage.get_data(query) == updated
    storage.delete_data(query)
    assert storage.read_bulk(TimeComplexityFilter(experiment_name="first")).items == [second]


def test_old_schema_is_reported_without_changing_existing_data(tmp_path):
    from sqlalchemy import create_engine, inspect, text

    connection = f"sqlite:///{tmp_path / 'old.db'}"
    engine = create_engine(connection)
    with engine.begin() as session:
        session.execute(text("CREATE TABLE time_complexity (id INTEGER PRIMARY KEY, results_times TEXT)"))
        session.execute(text("INSERT INTO time_complexity VALUES (1, '[0.1]')"))
    with pytest.raises(RuntimeError, match="old schema without generator_code"):
        AlchemyTimeComplexityStorage(connection).init()
    assert {column["name"] for column in inspect(engine).get_columns("time_complexity")} == {"id", "results_times"}
    with engine.connect() as session:
        assert session.execute(text("SELECT results_times FROM time_complexity")).scalar_one() == "[0.1]"
    engine.dispose()
