import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import SWMTest
from stattest_std.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([12, 12, 12, 12, 14, 14, 16, 16, 16, 16, 18], 3.66666666),
        ([18, 16, 16, 16, 16, 14, 14, 12, 12, 12, 12], 3.66666666),
        ([-1.71228079, -0.86710019, 0.29950617, 1.18632683, -0.13929811, -1.47008114,
          -1.29073683, 1.18998087, 0.80807576, 0.45558552], 0.07474902435493411),
    ],
)
class TestCaseSWMTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SWMTest()
