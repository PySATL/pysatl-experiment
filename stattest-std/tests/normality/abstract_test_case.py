import pytest


class AbstractTestCase:

    def test_execute_statistic(self, data, result, statistic_test):
        statistic = statistic_test.execute_statistic(data)
        print(statistic)
        assert result == pytest.approx(statistic, 0.00001)
