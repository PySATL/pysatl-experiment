import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import FilliTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-4, -2, 0, 1, 5, 6, 8], 0.9854095718708367),
    ],
)
class TestCaseFilliNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return FilliTest()
