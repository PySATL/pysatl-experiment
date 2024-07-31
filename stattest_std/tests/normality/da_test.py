import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import DATest
from stattest_std.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1, 0, 1], 0),
    ],
)
class TestCaseDATest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DATest()
