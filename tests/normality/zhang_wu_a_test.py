import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/zhang_wu_a_test.py
from stattest_std.src.stat_tests.normality_tests import ZhangWuATest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import ZhangWuATest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/zhang_wu_a_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.0968987,  1.7392081,  0.9674481, -0.3418871, -0.5659707,  1.0234917,  1.0958103], 1.001392),
        ([0.31463996, 0.17626475, -0.01481709, 0.25539075, 0.64605810, 0.64965352, -0.36176169, -0.59318222,
          -0.44131251, 0.41216214], 1.225743),
    ],
)
class TestCaseZhangWuCNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return ZhangWuATest()
