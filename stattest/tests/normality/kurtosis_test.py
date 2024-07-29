import pytest as pytest

from stattest.src.cr_tests.criteria.normality_tests import KurtosisTest
from stattest.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.3048235214240873),
    ],
)
class TestCaseKurtosisTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return KurtosisTest()
