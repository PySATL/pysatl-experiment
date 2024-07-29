import pytest as pytest

from stattest.src.cr_tests.criteria.normality_tests import DATest  # TODO: ????
from stattest.tests.normality.abstract_test_case import AbstractTestCase


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
