import pytest

from stattest.test import MSFWeibullTestStatistic
from tests.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        ([0.92559015, 0.9993195, 1.15193844, 0.84272073, 0.97535299, 0.83745092, 0.92161732, 1.02751619, 0.90079826,
          0.79149641], 0.67173),
    ],
)
class TestCaseMSFTest(AbstractTestCase):

    def test_execute_statistic(self, data, result, statistic_test):
        statistic = statistic_test.execute_statistic(data)
        assert result == pytest.approx(statistic, 0.01)

    @pytest.fixture
    def statistic_test(self):
        return MSFWeibullTestStatistic()
