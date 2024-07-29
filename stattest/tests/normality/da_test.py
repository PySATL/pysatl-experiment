import pytest as pytest

from stattest.test.normality import DATest  # TODO: ????
from stattest.tests.normality.AbstractTestCase import AbstractTestCase


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
