import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/kurtosis_test.py
from stattest_std.src.stat_tests.normality_tests import KurtosisTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import KurtosisTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/kurtosis_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.3048235214240873),
    ],
)
class TestCaseKurtosisNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return KurtosisTest()
