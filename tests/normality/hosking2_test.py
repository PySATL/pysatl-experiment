import pytest as pytest

from stattest.test.normal import Hosking2Test
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.52179225, -0.07079375, 0.96500281, 0.65256255, 0.71376323, 0.18295605, 0.31265772], 13.27192),
        ([-0.9352061, -1.0456637, 0.7134893, 1.6715891, 1.7931811, -0.1422531, 0.9682729, 0.2980237, 0.8548988,
          -0.8224675], 1.693243),
    ],
)
class TestCaseHosking2Test(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return Hosking2Test()
