import pytest as pytest
from numpy import nan

from stattest.test.normal import DAPNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 13.034263121192582),
        ([16, 18, 16, 14, 12, 12, 16, 18, 16, 14, 12, 12], 2.5224),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 1.2153434753677772),  # Negative values test
    ],
)
class TestCaseDAPNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return DAPNormalityTest()
