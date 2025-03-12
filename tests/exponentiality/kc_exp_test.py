import pytest as pytest
from numpy import nan

from stattest.test.exponent import KCTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 2.407337243970289),
        ([i for i in range(1, 10)], 2.5321283353212976),
        ([i for i in range(1, 50)], 4.341932979613143),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 6.767360569535781),  # Negative values test
    ],
)
class TestCaseKCExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return KCTestExp()
