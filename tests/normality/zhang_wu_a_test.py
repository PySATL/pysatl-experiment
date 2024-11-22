import pytest as pytest

from stattest.test.normal import ZhangWuATest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.0968987,  1.7392081,  0.9674481, -0.3418871, -0.5659707,  1.0234917,  1.0958103], 1.001392),
        ([0.31463996, 0.17626475, -0.01481709, 0.25539075, 0.64605810, 0.64965352, -0.36176169, -0.59318222,
          -0.44131251, 0.41216214], 1.225743),
    ],
)
@pytest.mark.skip(reason="no way of currently testing this")
class TestCaseZhangWuATest(AbstractTestCase):

    def test_execute_statistic(self, data, result, statistic_test):
        statistic = statistic_test.execute_statistic(data)
        assert result == pytest.approx(statistic, 0.1)

    @pytest.fixture
    def statistic_test(self):
        return ZhangWuATest()
