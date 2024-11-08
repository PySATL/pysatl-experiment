from typing import override

import pytest

from stattest_std.tests.abstract_test_case import AbstractTestCase
from stattest_std.src.stat_tests.exponentiality_tests import ExponentialityTest


class AbstractExponentialityTestCase(AbstractTestCase):  # TODO: add generics?

    @staticmethod
    @override
    def test_execute_statistic(data, result, statistic_test: ExponentialityTest):
        statistic = statistic_test.execute_statistic(data)
        print(statistic)
        assert result == pytest.approx(statistic, 0.00001)
