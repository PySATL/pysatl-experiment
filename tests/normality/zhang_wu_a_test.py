import pytest as pytest

from stattest.test.normal import ZhangWuANormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                -1.0968987,
                1.7392081,
                0.9674481,
                -0.3418871,
                -0.5659707,
                1.0234917,
                1.0958103,
            ],
            1.001392,
        ),
        (
            [
                0.31463996,
                0.17626475,
                -0.01481709,
                0.25539075,
                0.64605810,
                0.64965352,
                -0.36176169,
                -0.59318222,
                -0.44131251,
                0.41216214,
            ],
            1.225743,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.16232061118184815),  # Negative values test
    ],
)
@pytest.mark.skip(reason="no way of currently testing this")
class TestCaseZhangWuCNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return ZhangWuANormalityTest()
