import pytest as pytest

from stattest.test.normal import JBNormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 6.982848237344646),
        (
            [
                0.30163062,
                -1.17676177,
                -0.883211,
                0.55872679,
                2.04829646,
                0.66029436,
                0.83445286,
                0.72505429,
                1.25012578,
                -1.11276931,
            ],
            0.44334632590843914,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 0.7435185185185184),  # Negative values test
    ],
)
class TestCaseJBNormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return JBNormalityTest()
