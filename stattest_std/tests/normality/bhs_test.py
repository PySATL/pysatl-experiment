import pytest as pytest

from stattest_std.src.stat_tests.normality_tests import BHSTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.67723972, 0.39432278, -0.08296916, -2.32715064, 2.13139707, 0.76899427, 1.70418919], 0.4687209),
        ([0.3837459, -2.4917339, 0.6754353, -0.5634646, -1.3273973, 0.4896063,
          1.0786708, -0.1585859, -1.0140335, 1.0448026], -0.5880094),
    ],
)
@pytest.mark.skip(reason="no way of currently testing this")  # TODO: remove skip when ready
class TestCaseBHSNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return BHSTest()
