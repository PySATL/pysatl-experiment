import pytest as pytest

from stattest.test.normal import Hosking1NormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                -0.17746565,
                0.36878289,
                0.14037068,
                -0.56292004,
                2.02953048,
                0.63754044,
                -0.05821471,
            ],
            31.26032,
        ),
        (
            [
                0.07532721,
                0.17561663,
                -0.45442472,
                -0.31402998,
                -0.36055484,
                0.46426559,
                0.18860127,
                -0.18712276,
                0.12134652,
                0.25866486,
            ],
            3.347533,
        ),
    ],
)
class TestCaseHosking1NormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return Hosking1NormalityTest()
