import pytest as pytest

from stattest.test.exponent import HG2TestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 11.810123785066443),
        ([i for i in range(1, 10)], 20.755640715745614),
        ([i for i in range(1, 50)], 756.0135513956228),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1.2711662185480854),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 18.62437981246421),  # Negative values test
    ],
)
class TestCaseHG2ExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return HG2TestExp()
