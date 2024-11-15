import pytest as pytest

from stattest.test.normal import FilliTest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-4, -2, 0, 1, 5, 6, 8], 0.9854095718708367),
    ],
)
class TestCaseFilliTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return FilliTest()
