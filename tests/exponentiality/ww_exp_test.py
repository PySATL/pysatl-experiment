import pytest as pytest

from stattest.test.exponent import WWTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 7.0),
        ([i for i in range(1, 10)], 9.0),
        ([i for i in range(1, 50)], 49.0),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -0.0),  # Negative values test
    ],
)
class TestCaseWWExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return WWTestExp()
