import pytest
from pysatl.criterion import (
    AndersonDarlingWeibullGofStatistic,
    Chi2PearsonWeibullGofStatistic,
    CrammerVonMisesWeibullGofStatistic,
    KolmogorovSmirnovWeibullGofStatistic,
    LillieforsWeibullGofStatistic,
    LOSWeibullGofStatistic,
)

from stattest.resolvers.test_resolver import TestResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("AndersonDarlingWeibullGofStatistic", AndersonDarlingWeibullGofStatistic),
        ("Chi2PearsonWeibullGofStatistic", Chi2PearsonWeibullGofStatistic),
        ("CrammerVonMisesWeibullGofStatistic", CrammerVonMisesWeibullGofStatistic),
        ("KolmogorovSmirnovWeibullGofStatistic", KolmogorovSmirnovWeibullGofStatistic),
        ("LillieforsWeibullGofStatistic", LillieforsWeibullGofStatistic),
        ("LOSWeibullGofStatistic", LOSWeibullGofStatistic),
    ],
)
def test_load_without_params(name, expected):
    test = TestResolver.load(name)

    assert test is not None
    assert type(test) is expected
