import pytest as pytest

from stattest.src.cr_tests.criteria.normality_tests import ChenShapiroTest
from stattest.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.93797412, -0.33927015, -0.57280736, 0.03294079, 0.48674056, -0.52471379, 1.15231162], -0.07797202),
        ([-0.8732478, 0.6104841, 1.1886920, 0.3229907, 1.4729158, 0.5256972, -0.4902668, -0.8249011,
          -0.7751734, -1.8370833], -0.1217789),
    ],
)
class TestCaseZhangWuCTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ChenShapiroTest()
