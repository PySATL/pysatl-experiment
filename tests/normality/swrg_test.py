import pytest as pytest

from stattest.test.normal import SWRGTest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.2361394,  0.3353304,  1.0837427,  1.7284429, -0.5890293, -0.2175157, -0.3615631], 0.9120115),
        ([-0.38611393,  0.40744855,  0.01385485, -0.80707299, -1.33020278,  0.53527066,
          0.35588475, -0.44262575,  0.28699128, -0.66855218], 0.9092612),
    ],
)
class TestCaseZhangWuCTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SWRGTest()
