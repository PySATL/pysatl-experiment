import pytest as pytest

from stattest.src.cr_tests.criteria.normality_tests import DAPTest
from stattest.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 13.034263121192582),
        ([16, 18, 16, 14, 12, 12, 16, 18, 16, 14, 12, 12], 2.5224),
    ],
)
class TestCaseDAPTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DAPTest()
