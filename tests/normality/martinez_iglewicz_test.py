import pytest as pytest
from numpy import nan

from stattest.test.normal import MartinezIglewiczNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                0.42240539,
                -1.05926060,
                1.38703979,
                -0.69969283,
                -0.58799872,
                0.45095572,
                0.07361136,
            ],
            1.081138,
        ),
        (
            [
                -0.6930954,
                -0.1279816,
                0.7552798,
                -1.1526064,
                0.8638102,
                -0.5517623,
                0.3070847,
                -1.6807102,
                -1.7846244,
                -0.3949447,
            ],
            1.020476,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 1.0906156152956765),  # Negative values test
    ],
)
class TestCaseMartinezIglewiczNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return MartinezIglewiczNormalityTest()
