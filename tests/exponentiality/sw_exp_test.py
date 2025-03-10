import pytest as pytest

from stattest.test.exponent import SWTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.375),
        ([i for i in range(1, 10)], 0.3),
        ([i for i in range(1, 50)], 0.06),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.16232061118184815),  # Negative values test
    ],
)
class TestCaseSWExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return SWTestExp()
