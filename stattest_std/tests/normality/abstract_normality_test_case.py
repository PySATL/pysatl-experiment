from typing import override

import pytest

from stattest_std.tests.abstract_test_case import AbstractTestCase
from stattest_std.src.stat_tests.normality_tests import NormalityTest


class AbstractNormalityTestCase(AbstractTestCase):

    @staticmethod
    @override
    def test_execute_statistic(data, result, statistic_test: NormalityTest):
        statistic = statistic_test.execute_statistic(data)
        print(statistic)
        assert result == pytest.approx(statistic, 0.00001)
