import pytest
from typing_extensions import override

from stattest.test.exponent import AbstractExponentialityTestStatistic
from tests.abstract_test_case import AbstractTestCase


class AbstractExponentialityTestCase(AbstractTestCase):

    @staticmethod
    @override
    def test_execute_statistic(data, result, statistic_test: AbstractExponentialityTestStatistic):
        statistic = statistic_test.execute_statistic(data)
        assert result == pytest.approx(statistic, 0.00001)
