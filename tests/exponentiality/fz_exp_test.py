import pytest as pytest
from numpy import nan

from stattest.test.exponent import FZTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.3074337694597331),
        ([i for i in range(1, 10)], 0.33996298180722573),
        ([i for i in range(1, 50)], 0.6860597085041713),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 1.6265090069613914),  # Negative values test
    ],
)
class TestCaseFZExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return FZTestExp()
