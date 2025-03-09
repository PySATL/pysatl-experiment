import pytest

from stattest.experiment.test import PowerCalculationWorker
from stattest.persistence import RvsDbStore, ResultDbStore, CriticalValueDbStore
from stattest.resolvers.store_resolver import StoreResolver
from stattest.resolvers.worker_resolver import WorkerResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("RvsDbStore", RvsDbStore),
        ("CriticalValueDbStore", CriticalValueDbStore),
        ("ResultDbStore", ResultDbStore)
    ],
)
def test_load_without_params(name, expected):
    # Always load stores with params!
    worker = StoreResolver.load(name)

    assert worker is not None
    # assert type(worker) is expected
