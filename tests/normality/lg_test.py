import pytest as pytest

from stattest.test.normal import LooneyGulledgeNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 170, 182, 195], 0.956524208286),
    ],
)
class TestCaseLGNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return LooneyGulledgeNormalityTest()
