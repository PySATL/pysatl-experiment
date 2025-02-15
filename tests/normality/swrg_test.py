import pytest as pytest

from stattest.test.normal import SWRGNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                0.2361394,
                0.3353304,
                1.0837427,
                1.7284429,
                -0.5890293,
                -0.2175157,
                -0.3615631,
            ],
            0.9120115,
        ),
        (
            [
                -0.38611393,
                0.40744855,
                0.01385485,
                -0.80707299,
                -1.33020278,
                0.53527066,
                0.35588475,
                -0.44262575,
                0.28699128,
                -0.66855218,
            ],
            0.9092612,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.9188664521936415),  # Negative values test
    ],
)
class TestCaseZhangWuCNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return SWRGNormalityTest()
