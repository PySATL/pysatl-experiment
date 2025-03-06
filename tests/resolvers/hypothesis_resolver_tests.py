import pytest

from stattest.experiment.hypothesis import NormalHypothesis, WeibullHypothesis
from stattest.resolvers.hypothesis_resolver import HypothesisResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("NormalHypothesis", NormalHypothesis),
        ("WeibullHypothesis", WeibullHypothesis),
    ],
)
def test_load_without_params(name, expected):
    hypothesis = HypothesisResolver.load(name)

    assert hypothesis is not None
    assert type(hypothesis) is expected
