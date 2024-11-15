import pytest as pytest

from stattest.test.normal import JBTest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 6.982848237344646),
        ([0.30163062, -1.17676177, -0.883211, 0.55872679, 2.04829646, 0.66029436,
          0.83445286, 0.72505429, 1.25012578, -1.11276931], 0.44334632590843914),
    ],
)
class TestCaseJBTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return JBTest()
