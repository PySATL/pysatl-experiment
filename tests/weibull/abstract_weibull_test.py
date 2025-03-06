from abc import ABC

import pytest
from typing_extensions import override

from tests.abstract_test_case import AbstractTestCase


class AbstractWeibullTestCase(AbstractTestCase, ABC):
    @staticmethod
    @override
    def test_execute_statistic(data, result, statistic_test):
        statistic = statistic_test.execute_statistic(data)
        assert result == pytest.approx(statistic, 0.01)
