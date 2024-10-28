import pytest as pytest

from stattest.test.normal import SFTest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.5461357, 0.8049704, -1.2676556, 0.1912453, 1.4391551, 0.5352138, -1.6212611, 0.1015035, -0.2571793,
          0.8756286], 0.93569),
    ],
)
class TestCaseSFTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SFTest()
