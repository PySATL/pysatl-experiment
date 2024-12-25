import pytest as pytest

from stattest.test.exponent import EPSTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 1.9805506001800177),
        ([i for i in range(1, 10)], 2.8402544224554234),
        ([i for i in range(1, 50)], 22.49300240015063),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.16232061118184815),  # Negative values test
    ],
)
class TestCaseEPSExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return EPSTestExp()
