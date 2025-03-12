import pytest as pytest

from stattest.test.exponent import HPTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.12380952380952381),
        ([i for i in range(1, 10)], 0.1349206349206349),
        ([i for i in range(1, 50)], 0.1614560717904183),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0.0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.7000000000000001),  # Negative values test
    ],
)
class TestCaseHPExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return HPTestExp()
