import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/skew_test.py
from stattest_std.src.stat_tests.normality_tests import SkewTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import SkewTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/skew_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 182, 195, 236], 2.7788579769903414),
    ],
)
class TestCaseSkewNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SkewTest()
