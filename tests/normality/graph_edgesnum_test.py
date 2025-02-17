import pytest as pytest

from stattest.test.normal import GraphEdgesNumberNormTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-0.264, 0.031, 0.919, 1.751, -0.038, 0.133, 0.643, -0.480, 0.094, -0.527], 9),
        ([1.311, 3.761, 0.415, 0.764, 0.100, -0.028, -1.516, -0.108, 2.248, 0.229], 11),
    ],
)
class TestCaseGraphEdgesNumbernormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return GraphEdgesNumberNormTest()
