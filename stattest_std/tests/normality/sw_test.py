import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import SWTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([16, 18, 16], 0.75),
        ([16, 18, 16, 14], 0.9446643),
        ([16, 18, 16, 14, 15], 0.955627),
        ([38.7, 41.5, 43.8, 44.5, 45.5, 46.0, 47.7, 58.0], 0.872973),
    ],
)
class TestCaseSWNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SWTest()
