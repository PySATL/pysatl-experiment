import pytest as pytest
from numpy import nan

from stattest.test.normal import KurtosisNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.3048235214240873),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.21690187507466038),  # Negative values test
    ],
)
class TestCaseKurtosisNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return KurtosisNormalityTest()
