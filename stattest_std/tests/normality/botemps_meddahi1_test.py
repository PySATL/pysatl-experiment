import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import BontempsMeddahi1Test
from stattest_std.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.5803773, -1.3941189,  1.4266496,  0.4229516,  1.2052829, -0.7798392, -0.2476446], 0.2506808),
        ([0.05518574, -0.09918900, -0.25097539,  0.45345120,  1.01584731,  0.45844901,
          0.79256755,  0.36811349, -0.56170844,  3.15364608], 4.814269),
    ],
)
class TestCaseZhangWuCTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return BontempsMeddahi1Test()
