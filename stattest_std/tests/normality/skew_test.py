import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import SkewTest
from stattest_std.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.7788579769903414),
    ],
)
class TestCaseSkewTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SkewTest()
