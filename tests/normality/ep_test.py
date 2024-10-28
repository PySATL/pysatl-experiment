import pytest as pytest

from stattest.test.normal import EPTest
from tests.AbstractTestCase import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([
             5.50, 5.55, 5.57, 5.34, 5.42, 5.30, 5.61, 5.36, 5.53, 5.79,
             5.47, 5.75, 4.88, 5.29, 5.62, 5.10, 5.63, 5.68, 5.07, 5.58,
             5.29, 5.27, 5.34, 5.85, 5.26, 5.65, 5.44, 5.39, 5.46
         ], 0.05191694742233466),
    ],
)
class TestCaseEPTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return EPTest()
