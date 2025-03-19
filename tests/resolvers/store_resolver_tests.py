import pytest

from stattest.persistence import CriticalValueDbStore, ResultDbStore, RvsDbStore
from stattest.resolvers.store_resolver import StoreResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("RvsDbStore", RvsDbStore),
        ("CriticalValueDbStore", CriticalValueDbStore),
        ("ResultDbStore", ResultDbStore),
    ],
)
def test_load_without_params(name, expected):
    # Always load stores with params!
    worker = StoreResolver.load(name)

    assert worker is not None
    # assert type(worker) is expected
