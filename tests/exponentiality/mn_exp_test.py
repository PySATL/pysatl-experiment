import pytest as pytest
from numpy import nan, inf

from stattest.test.exponent import MNTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.4088014982195586),
        ([i for i in range(1, 10)], 0.3902030280320402),
        ([i for i in range(1, 50)], 0.3086611450607788),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -inf),  # Negative values test
    ],
)
class TestCaseMNExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return MNTestExp()
