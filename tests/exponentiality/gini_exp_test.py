import pytest as pytest
from numpy import nan

from stattest.test.exponent import GiniTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.3333333333333333),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.3333333333333333),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -0.5037037037037037),  # Negative values test
    ],
)
class TestCaseGiniExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return GiniTestExp()
