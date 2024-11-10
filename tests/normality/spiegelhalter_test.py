import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/spiegelhalter_test.py
from stattest_std.src.stat_tests.normality_tests import SpiegelhalterTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import SpiegelhalterTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/spiegelhalter_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.31669223,  2.22819380, -0.27391944, -1.57616900, -2.21675399, -0.01497801, -1.65492071], 1.328315),
        ([-1.6412500, -1.1946111,  1.1054937, -0.4210709, -1.1736754, -1.1750840,
          1.3267088, -0.3299987, -0.5767829, -1.4114579], 1.374628),
    ],
)
class TestCaseSpiegelhalterNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SpiegelhalterTest()
