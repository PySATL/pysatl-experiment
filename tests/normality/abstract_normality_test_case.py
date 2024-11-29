from abc import ABC

import pytest
from typing_extensions import override

from stattest.test.normal import AbstractNormalityTestStatistic
from tests.abstract_test_case import AbstractTestCase


class AbstractNormalityTestCase(AbstractTestCase, ABC):
    @staticmethod
    @override
    def test_execute_statistic(
        data, result, statistic_test: AbstractNormalityTestStatistic
    ):
        statistic = statistic_test.execute_statistic(data)
        assert result == pytest.approx(statistic, 0.00001)
