import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/dap_test.py
from stattest_std.src.stat_tests.normality_tests import DAPTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import DAPTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/dap_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 13.034263121192582),
        ([16, 18, 16, 14, 12, 12, 16, 18, 16, 14, 12, 12], 2.5224),
    ],
)
class TestCaseDAPNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DAPTest()
