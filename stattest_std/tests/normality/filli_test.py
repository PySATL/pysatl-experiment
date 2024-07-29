import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import FilliTest
from stattest_std.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-4, -2, 0, 1, 5, 6, 8], 0.9854095718708367),
    ],
)
class TestCaseFilliTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return FilliTest()
