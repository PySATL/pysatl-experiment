import pytest as pytest

from stattest.test.exponent import GraphMaxDegreeExpTest
from tests.exponentiality.abstract_exponentiality_test_case import AbstractExponentialityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.713, 0.644, 2.625, 0.740, 0.501, 0.185, 0.982, 1.028, 1.152, 0.267], 4),
        ([0.039, 3.036, 0.626, 1.107, 0.139, 1.629, 0.050, 0.118, 0.978, 2.699], 3),
    ],
)
class TestCaseGraphMaxDegreeExponentialityTest(AbstractExponentialityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return GraphMaxDegreeExpTest()
