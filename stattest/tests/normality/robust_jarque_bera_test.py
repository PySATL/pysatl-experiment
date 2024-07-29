import pytest as pytest

from stattest.src.cr_tests.criteria.normality_tests import RobustJarqueBeraTest
from stattest.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1.2318068, -0.3417207, -1.2044307, -0.7724564, -0.2145365, -1.0119879,  0.2222634], 0.8024895),
        ([-1.0741031,  1.3157369,  2.7003935,  0.8843286, -0.4361445, -0.3000996, -0.2710125,
          -0.6915687, -1.7699595,  1.3740694], 0.4059704),

    ],
)
class TestCaseRobustJarqueBeraTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return RobustJarqueBeraTest()
