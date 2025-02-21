import pytest as pytest

from stattest.test.normal import SkewNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.7788579769903414),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -1.080877907978914),  # Negative values test
    ],
)
class TestCaseSkewNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return SkewNormalityTest()
