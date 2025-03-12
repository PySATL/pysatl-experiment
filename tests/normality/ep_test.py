import pytest as pytest
from numpy import nan

from stattest.test.normal import EPNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                5.50,
                5.55,
                5.57,
                5.34,
                5.42,
                5.30,
                5.61,
                5.36,
                5.53,
                5.79,
                5.47,
                5.75,
                4.88,
                5.29,
                5.62,
                5.10,
                5.63,
                5.68,
                5.07,
                5.58,
                5.29,
                5.27,
                5.34,
                5.85,
                5.26,
                5.65,
                5.44,
                5.39,
                5.46,
            ],
            0.05191694742233466,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.10204382727741823),  # Negative values test
    ],
)
class TestCaseEPNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return EPNormalityTest()
