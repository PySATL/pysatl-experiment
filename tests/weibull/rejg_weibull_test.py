import pytest

from stattest.test import REJGWeibullTestStatistic
from tests.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        ([0.92559015, 0.9993195, 1.15193844, 0.84272073, 0.97535299, 0.83745092, 0.92161732, 1.02751619, 0.90079826,
          0.79149641], 0.84064),
    ],
)
class TestCaseREJGTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return REJGWeibullTestStatistic()
