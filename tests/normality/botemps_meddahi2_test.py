import pytest as pytest

from stattest.test.normal import BontempsMeddahi2Test
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.16956851, -1.88725716, -0.09051621, -0.84191408, -0.65989921, -0.22018994, -0.12274684], 1.155901),
        ([-2.1291160, -1.2046194, -0.9706029, 0.1458201, 0.5181943, -0.9769141, -0.8174199, 0.2369553,
          0.4190111, 0.6978357], 1.170676),
    ],
)
class TestCaseZhangWuCTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return BontempsMeddahi2Test()
