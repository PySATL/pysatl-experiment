import pytest as pytest

from stattest.test.exponent import AHSTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-0.5, 1.7, 1.2, 2.2, 0, -3.2768, 0.42], -0.37900874635568516),
        ([1.5, 2.7, -3.8, 4.6, -0.5, -0.6, 0.7, 0.8, -0.9, 10], -0.41),
        ([i for i in range(1, 10)], 0.33607681755829905),
        ([i for i in range(1, 50)], 0.26540812076600734),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -0.811),  # Negative values test
    ],
)
class TestCaseAHSExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return AHSTestExp()
