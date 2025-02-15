import pytest as pytest

from stattest.test.normal import LooneyGulledgeNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 170, 182, 195], 0.956524208286),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.9709603553923633),  # Negative values test
    ],
)
class TestCaseLGNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return LooneyGulledgeNormalityTest()
