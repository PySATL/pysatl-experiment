import pytest as pytest

from stattest.test.exponent import EPTestExp
from tests.exponentiality.abstract_exponentiality_test_case import \
    AbstractExponentialityTestCase


@pytest.mark.parametrize(  # TODO: actual test (7; 10)
    ("data", "result"),
    [
        ([1, 2, 3, 4, 5, 6, 7], -1.5476370552787166),
        ([1, 2, -3, 4, -5, -6, 7, 8, -9, 10], 50597.27324595228),
    ],
)
@pytest.mark.skip(reason="fix test and check")
class TestCaseEPExponentialityTest(AbstractExponentialityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return EPTestExp()
