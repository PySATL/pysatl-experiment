import pytest as pytest

from stattest.test.exponent import DSPTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.7857142857142857),
        ([i for i in range(1, 10)], 0.7916666666666666),
        ([i for i in range(1, 50)], 0.7810374149659864),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.28888888888888886),  # Negative values test
    ],
)
class TestCaseDSPExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return DSPTestExp()
