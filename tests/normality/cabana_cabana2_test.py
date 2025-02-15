import pytest as pytest

from stattest.test.normal import CabanaCabana2NormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                -0.2115733,
                -0.8935314,
                -0.1916746,
                0.2805032,
                1.3372893,
                -0.4324158,
                2.8578810,
            ],
            0.2497146,
        ),
        (
            [
                0.99880346,
                -0.07557944,
                0.25368407,
                -1.20830967,
                -0.15914329,
                0.16900984,
                0.99395022,
                -0.28167969,
                0.11683112,
                0.68954236,
            ],
            0.1238103,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.36999299233310545),  # Negative values test
    ],
)
class TestCaseCabanaCabana2NormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return CabanaCabana2NormalityTest()
