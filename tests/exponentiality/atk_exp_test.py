import pytest as pytest

from stattest.test.exponent import ATKTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.007564336567134994),
        ([i for i in range(1, 10)], 0.008258155370940656),
        ([i for i in range(1, 50)], 0.016733870931046946),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.16232061118184815),  # Negative values test
    ],
)
class TestCaseATKExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return ATKTestExp()
