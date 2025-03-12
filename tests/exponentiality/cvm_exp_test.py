import pytest as pytest
from numpy import nan

from stattest.test.exponent import CVMTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.1285081983260836),
        ([i for i in range(1, 10)], 0.14728440083505995),
        ([i for i in range(1, 50)], 0.5794331711413386),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.06943545873682137),  # Negative values test
    ],
)
class TestCaseCVMExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return CVMTestExp()
