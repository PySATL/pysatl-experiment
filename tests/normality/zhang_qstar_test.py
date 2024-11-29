import pytest as pytest

from stattest.test.normal import ZhangQStarNormalityTest
from tests.normality.abstract_normality_test_case import \
    AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.002808107, -0.366738714, 0.627663491, 0.459724293, 0.044694653,
          1.096110474, -0.492341832, 0.708343932, 0.247694191, 0.523295664, 0.234479385], 0.0772938),
        ([0.3837459, -2.4917339, 0.6754353, -0.5634646, -1.3273973, 0.4896063,
          1.0786708, -0.1585859, -1.0140335, 1.0448026], -0.5880094),
    ],
)
class TestCaseZhangQStarNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ZhangQStarNormalityTest()
