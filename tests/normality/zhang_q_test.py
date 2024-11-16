import pytest as pytest

from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
from stattest.test.normal import ZhangQNormalityTest


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([1.84917102, -0.11520399, -0.99425682, -0.02146024,  1.90311564,  1.10073929,  0.26444036,  1.46165119,
          1.65611589,  0.14613976,  0.29509227], 0.03502227),
        ([-1.21315374, -0.19765354,  0.46560179, -1.48894141, -0.57958644, -0.87905499,
          2.25757863, -0.83696957,  0.01074617, -0.34492908], -0.2811746),
    ],
)
class TestCaseZhangQNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ZhangQNormalityTest()
