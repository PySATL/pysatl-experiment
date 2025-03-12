import pytest as pytest

from stattest.test.exponent import LZTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.21428571428571427),
        ([i for i in range(1, 10)], 0.2222222222222222),
        ([i for i in range(1, 50)], 0.24489795918367346 ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.8333333333333334),  # Negative values test
    ],
)
class TestCaseLZExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return LZTestExp()
