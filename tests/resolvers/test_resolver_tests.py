import pytest

from stattest.resolvers.test_resolver import TestResolver
from stattest.test import ADWeibullTest, Chi2PearsonWiebullTest, CrammerVonMisesWeibullTest, KSWeibullTest, \
    LillieforsWiebullTest, LOSWeibullTestStatistic


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("ADWeibullTest", ADWeibullTest),
        ("Chi2PearsonWiebullTest", Chi2PearsonWiebullTest),
        ("CrammerVonMisesWeibullTest", CrammerVonMisesWeibullTest),
        ("KSWeibullTest", KSWeibullTest),
        ("LillieforsWiebullTest", LillieforsWiebullTest),
        ("LOSWeibullTestStatistic", LOSWeibullTestStatistic)
    ],
)
def test_load_without_params(name, expected):
    test = TestResolver.load(name)

    assert test is not None
    assert type(test) is expected
