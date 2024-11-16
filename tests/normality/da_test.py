""" # TODO: check this test
import pytest as pytest

from stattest.test.normal import DANormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1, 0, 1], 0),
    ],
)
class TestCaseDANormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DATest()
"""