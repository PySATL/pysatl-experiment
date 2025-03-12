import pytest as pytest
from numpy import nan

from stattest.test.exponent import HMTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 1.0),
        ([i for i in range(1, 10)], 1.0),
        ([i for i in range(1, 50)], 1.0 ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 2.85),  # Negative values test
    ],
)
class TestCaseHMExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return HMTestExp()
