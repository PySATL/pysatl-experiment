import pytest

from stattest.experiment.test import PowerCalculationWorker
from stattest.resolvers.worker_resolver import WorkerResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("PowerCalculationWorker", PowerCalculationWorker)
    ],
)
def test_load_without_params(name, expected):
    # Always load workers with params!
    worker = WorkerResolver.load(name)

    assert worker is not None
    # assert type(worker) is expected
