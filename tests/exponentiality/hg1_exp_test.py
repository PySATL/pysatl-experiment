import pytest as pytest

from stattest.test.exponent import HG1TestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 3.13843865275808),
        ([i for i in range(1, 10)], 4.119840182570562),
        ([i for i in range(1, 50)], 24.038298299599298),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0.8874540154908189),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 3.8874540154908193),  # Negative values test
    ],
)
class TestCaseHG1ExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return HG1TestExp()
