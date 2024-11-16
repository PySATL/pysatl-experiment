import pytest

from stattest.test.weibull import KSWeibullTest
from tests.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        ([0.38323312, -1.10386561, 0.75226465, -2.23024566, -0.27247827, 0.95926434, 0.42329541, -0.11820711,
          0.90892169, -0.29045373], 0.686501978410317),
    ],
)
class TestCaseKSTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return KSWeibullTest()