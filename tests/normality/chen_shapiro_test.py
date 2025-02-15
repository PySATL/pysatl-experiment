import pytest as pytest

from stattest.test.normal import ChenShapiroNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                0.93797412,
                -0.33927015,
                -0.57280736,
                0.03294079,
                0.48674056,
                -0.52471379,
                1.15231162,
            ],
            -0.07797202,
        ),
        (
            [
                -0.8732478,
                0.6104841,
                1.1886920,
                0.3229907,
                1.4729158,
                0.5256972,
                -0.4902668,
                -0.8249011,
                -0.7751734,
                -1.8370833,
            ],
            -0.1217789,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -0.09844001872056364),  # Negative values test
    ],
)
class TestCaseZhangWuCNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return ChenShapiroNormalityTest()
