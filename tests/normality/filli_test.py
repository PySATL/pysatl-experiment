import pytest as pytest

from stattest.test.normal import FilliNormalityTest
from tests.normality.abstract_normality_test_case import \
    AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-4, -2, 0, 1, 5, 6, 8], 0.9854095718708367),
    ],
)
class TestCaseFilliNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return FilliNormalityTest()
