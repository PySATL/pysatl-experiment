"""Bounded writes, keyset reads and experiment isolation for stored samples."""

from dataclasses import replace

import pytest
from sqlalchemy import event

from pysatl_experiment.persistence.models.random_values import RandomValuesFilter, RandomValuesModel
from pysatl_experiment.persistence.random_values_iterator import RandomValuesIterator
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage


def sample(value=0.0, *, experiment="first", generator="normal", size=2):
    return RandomValuesModel(
        experiment_name=experiment,
        generator_code=generator,
        generator_parameters={"mean": value, "var": 1.0},
        sample_size=size,
        data=[value] * size,
    )


@pytest.fixture
def storage():
    store = AlchemyRandomValuesStorage("sqlite://")
    store.init()
    return store


def test_guard_requires_init():
    store = AlchemyRandomValuesStorage("sqlite://")
    query = RandomValuesFilter(experiment_name="first")
    operations = [
        lambda: store.count(query),
        lambda: store.read_bulk(query),
        lambda: store.delete(query),
        lambda: store.bulk_insert([]),
    ]
    for operation in operations:
        with pytest.raises(RuntimeError, match="not initialized"):
            operation()


@pytest.mark.parametrize("name", ["", " ", None, 7])
def test_experiment_name_is_required_and_nonempty(name):
    with pytest.raises(ValueError, match="experiment_name"):
        RandomValuesFilter(experiment_name=name)
    with pytest.raises(ValueError, match="experiment_name"):
        sample(experiment=name)


@pytest.mark.parametrize("size", [0, -1, True, 2.5])
def test_invalid_sample_sizes_are_rejected(size):
    with pytest.raises(ValueError, match="sample_size"):
        RandomValuesFilter(experiment_name="first", sample_size=size)


def test_declared_sample_size_matches_data():
    with pytest.raises(ValueError, match="sample_size"):
        replace(sample(), sample_size=3)


@pytest.mark.parametrize(
    ("generator", "size", "expected"),
    [
        (None, None, 4),
        ("normal", None, 2),
        (None, 2, 2),
        ("normal", 2, 1),
        ("missing", None, 0),
    ],
)
def test_read_count_and_delete_share_optional_filters(storage, generator, size, expected):
    storage.bulk_insert(
        sample(i, experiment=owner, generator=code, size=n)
        for i, owner in enumerate(["first", "second"])
        for code in ["normal", "laplace"]
        for n in [2, 3]
    )
    query = RandomValuesFilter(experiment_name="first", generator_code=generator, sample_size=size)
    assert storage.count(query) == expected
    rows = list(RandomValuesIterator(storage, query, batch_size=2))
    assert len(rows) == expected
    assert all(row.experiment_name == "first" for row in rows)
    assert storage.delete(query) == expected
    assert storage.count(query) == 0
    assert storage.count(RandomValuesFilter(experiment_name="first")) == 4 - expected
    assert storage.count(RandomValuesFilter(experiment_name="second")) == 4


def test_bulk_appends_duplicates_and_preserves_each_rows_metadata(storage):
    samples = [sample(1.5, experiment="007"), sample(2.5, experiment="007"), sample(1.5, experiment="007")]
    storage.bulk_insert(samples, batch_size=2)
    storage.bulk_insert(samples[:1])
    query = RandomValuesFilter(experiment_name="007")
    assert list(RandomValuesIterator(storage, query, batch_size=2)) == samples + samples[:1]
    assert storage.count(query) == 4  # Four samples, not eight numbers.


def test_batch_pagination_handles_id_gaps_and_partial_last_page(storage):
    storage.bulk_insert(sample(float(i), generator="discard" if i == 1 else "normal") for i in range(6))
    storage.delete(RandomValuesFilter(experiment_name="first", generator_code="discard"))
    query = RandomValuesFilter(experiment_name="first")
    first = storage.read_bulk(query, batch_size=2)
    second = storage.read_bulk(query, after_id=first.next_after_id, batch_size=2)
    third = storage.read_bulk(query, after_id=second.next_after_id, batch_size=2)
    assert [[s.data[0] for s in b.items] for b in [first, second, third]] == [[0, 2], [3, 4], [5]]
    assert first.next_after_id < second.next_after_id
    assert third.next_after_id is None


def test_empty_read(storage):
    batch = storage.read_bulk(RandomValuesFilter(experiment_name="empty"))
    assert batch.items == []
    assert batch.next_after_id is None


def test_bulk_write_consumes_input_incrementally_and_uses_bulk_sql(storage):
    query = RandomValuesFilter(experiment_name="first")
    inserts = []
    engine = storage._session_factory().kw["bind"]

    @event.listens_for(engine, "before_cursor_execute")
    def record_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT"):
            inserts.append((executemany, len(parameters)))

    def source():
        for i in range(5):
            if i == 2:
                assert storage.count(query) == 2
            if i == 4:
                assert storage.count(query) == 4
            yield sample(float(i))

    storage.bulk_insert(source(), batch_size=2)
    assert storage.count(query) == 5
    assert len(inserts) == 3
    assert inserts[:2] == [(True, 2), (True, 2)]


def test_failed_batch_preserves_only_previously_committed_batches(storage):
    broken = sample(3)
    broken.data.clear()
    with pytest.raises(ValueError, match="sample_size"):
        storage.bulk_insert([sample(0), sample(1), sample(2), broken], batch_size=2)
    query = RandomValuesFilter(experiment_name="first")
    assert storage.count(query) == 2
    storage.bulk_insert([sample(4)])  # The next operation has a clean session.
    assert [s.data[0] for s in RandomValuesIterator(storage, query)] == [0, 1, 4]


def test_separate_store_instances_keep_their_own_database(storage):
    other = AlchemyRandomValuesStorage("sqlite://")
    other.init()
    query = RandomValuesFilter(experiment_name="first")
    storage.bulk_insert([sample(1)])
    other.bulk_insert([sample(2), sample(3)])
    storage.init()  # Idempotent: does not reconnect to another in-memory database.
    assert storage.count(query) == 1
    assert other.count(query) == 2
    assert storage.read_bulk(query).items == [sample(1)]


@pytest.mark.parametrize("size", [0, -1, True, 1.5])
def test_invalid_batch_size(storage, size):
    with pytest.raises(ValueError, match="batch_size"):
        storage.bulk_insert([], batch_size=size)
    with pytest.raises(ValueError, match="batch_size"):
        storage.read_bulk(RandomValuesFilter(experiment_name="first"), batch_size=size)


@pytest.mark.parametrize("position", [0, -1, True, 1.5])
def test_invalid_read_position(storage, position):
    with pytest.raises(ValueError, match="after_id"):
        storage.read_bulk(RandomValuesFilter(experiment_name="first"), after_id=position)


def test_database_failure_rolls_back_the_current_batch(storage):
    broken = sample(3)
    broken.data = [object(), object()]  # Compression cannot encode these values.
    from sqlalchemy.exc import StatementError

    with pytest.raises(StatementError):
        storage.bulk_insert([sample(0), sample(1), sample(2), broken], batch_size=2)
    query = RandomValuesFilter(experiment_name="first")
    assert storage.count(query) == 2
    storage.bulk_insert([sample(4)])
    assert storage.count(query) == 3


def test_concurrent_writers_do_not_allocate_sample_numbers(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    connection = f"sqlite:///{tmp_path / 'parallel.sqlite'}"
    stores = [AlchemyRandomValuesStorage(connection) for _ in range(3)]
    for store in stores:
        store.init()

    def append(store):
        store.bulk_insert((sample(float(i)) for i in range(15)), batch_size=4)

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(append, stores))
    query = RandomValuesFilter(experiment_name="first")
    assert stores[0].count(query) == 45
    assert len(list(RandomValuesIterator(stores[0], query, batch_size=7))) == 45
