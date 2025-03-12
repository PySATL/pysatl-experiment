import pytest as pytest
from numpy import nan

from stattest.test.normal import FilliNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-4, -2, 0, 1, 5, 6, 8], 0.9854095718708367),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.9711698265330528),  # Negative values test
    ],
)
class TestCaseFilliNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return FilliNormalityTest()
