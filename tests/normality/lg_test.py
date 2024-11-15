import pytest as pytest

from stattest.test.normal import LooneyGulledgeTest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 170, 182, 195], 0.956524208286),
    ],
)
class TestCaseLGTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return LooneyGulledgeTest()
