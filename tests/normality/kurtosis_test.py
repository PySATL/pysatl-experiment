import pytest as pytest

from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
from stattest.test.normal import KurtosisNormalityTest


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.3048235214240873),
    ],
)
class TestCaseKurtosisNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return KurtosisNormalityTest()
