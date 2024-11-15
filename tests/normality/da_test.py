import pytest as pytest

from stattest.test.normal import DATest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1, 0, 1], 0),
    ],
)
class TestCaseDATest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DATest()
