import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/lg_test.py
from stattest_std.src.stat_tests.normality_tests import LooneyGulledgeTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import LooneyGulledgeTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/lg_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([148, 154, 158, 160, 161, 162, 166, 170, 170, 182, 195], 0.956524208286),
    ],
)
class TestCaseLGNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return LooneyGulledgeTest()
