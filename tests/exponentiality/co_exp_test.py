import pytest as pytest
from numpy import nan, inf

from stattest.test.exponent import COTestExp
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], 4.863554837932963),
        ([i for i in range(1, 10)], 5.990431555682576),
        ([i for i in range(1, 50)], 26.85362640237867),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], -inf),  # Negative values test
    ],
)
class TestCaseCOExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return COTestExp()
