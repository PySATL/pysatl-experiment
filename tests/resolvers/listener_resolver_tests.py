import pytest

from stattest.experiment.listener import TimeEstimationListener
from stattest.resolvers.listener_resolver import ListenerResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [("TimeEstimationListener", TimeEstimationListener)],
)
def test_load_without_params(name, expected):
    listener = ListenerResolver.load(name)

    assert listener is not None
    assert type(listener) is expected
