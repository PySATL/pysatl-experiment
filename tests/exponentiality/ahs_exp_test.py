import pytest as pytest

from stattest.test.exponent import AHSTestExp
from tests.exponentiality.abstract_exponentiality_test_case import (
    AbstractExponentialityTestCase,
)


# TODO: actual test (7; 10)
@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-0.5, 1.7, 1.2, 2.2, 0, -3.2768, 0.42], -0.37900874635568516),
        ([1.5, 2.7, -3.8, 4.6, -0.5, -0.6, 0.7, 0.8, -0.9, 10], -0.41),
    ],
)
@pytest.mark.skip(reason="fix test and check")
class TestCaseAHSExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return AHSTestExp()
