import pytest as pytest
from numpy import nan

from stattest.test.exponent import EPTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], -1.5476370552787166),
        ([i for i in range(1, 10)], -1.6857301742971205),
        ([i for i in range(1, 50)], -3.41280082738495),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -0.3434045153356423),  # Negative values test
    ],
)
class TestCaseEPExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return EPTestExp()
