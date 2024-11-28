import pytest as pytest

from stattest.test.exponent import ATKTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


# TODO: actual test (7; 10)
@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 0.007564336567134994),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.00858038457884382),
    ],
)
@pytest.mark.skip(reason="fix test and check")
class TestCaseATKExponentialityTest(AbstractExponentialityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ATKTestExp()
