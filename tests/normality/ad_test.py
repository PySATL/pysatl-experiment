import pytest as pytest

from stattest.test.normal import ADTestStatistic
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Normal with mean = 0, variance = 1
        ([16, 18, 16, 14, 12, 12, 16, 18, 16, 14, 12, 12], 0.6822883),
        ([1.0329650, -0.2861944,  0.1488185,  0.9907514, -0.3244450,  0.4430822, -0.1238494], 0.3753546),
        ([-0.21999313,  0.48724826,  0.87227246, -0.08396081, -0.12506021, -2.54337169,
          0.50740722, -0.15209779, -0.12694116, -1.09978690], 0.7747652),
    ],
)
class TestCaseADTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ADTestStatistic()
