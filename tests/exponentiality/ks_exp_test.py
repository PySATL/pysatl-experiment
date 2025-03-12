import pytest as pytest
from numpy import nan

from stattest.test.exponent import KSTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.38323312, 1.10386561, 0.75226465, 2.23024566, 0.27247827, 0.95926434, 0.42329541, 0.11820711,
          0.90892169, 0.29045373], 0.12690001008970853),
        ([i for i in range(1, 10)], 0.16529888822158656),
        ([i for i in range(1, 50)], 0.14644423212420637),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([4, 1, 6, -8, 4, 2, 0, -2, 0, 3], 2980.057987041728),  # Some garbage values test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.2),  # Negative values test
    ],
)
class TestCaseKSExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return KSTestExp()
