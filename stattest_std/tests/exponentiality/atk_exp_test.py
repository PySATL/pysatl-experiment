import pytest as pytest

from stattest_std.src.stat_tests.exponentiality_tests import ATKTestExp
from stattest_std.tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


# TODO: actual test (7; 10)
@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.007564336567134994),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.00858038457884382),
    ],
)
class TestCaseATKExponentialityTest(AbstractExponentialityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ATKTestExp()
