from typing_extensions import override

import pytest

from tests.abstract_test_case import AbstractTestCase
from stattest.test.normal import AbstractNormalityTestStatistic
from abc import ABC


class AbstractNormalityTestCase(AbstractTestCase, ABC):

    @staticmethod
    @override
    def test_execute_statistic(data, result, statistic_test: AbstractNormalityTestStatistic):
        statistic = statistic_test.execute_statistic(data)
        assert result == pytest.approx(statistic, 0.00001)
