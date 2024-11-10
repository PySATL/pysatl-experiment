import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/glen_leemis_barr_test.py
from stattest_std.src.stat_tests.normality_tests import GlenLeemisBarrTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import GlenLeemisBarrTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/glen_leemis_barr_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-0.2326386, 0.5440749, 0.9742477, 0.1979832, 1.7937705, -0.5430379, 1.5229193], 5.019177),
        ([0.43880197, 0.01657893, 0.11190411, 0.22168051, -0.83993220, -1.85572181, 0.07311574, -0.69846684, 0.54829821,
          -0.45549464], 12.54511),
    ],
)
class TestCaseGlenLeemisBarrNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return GlenLeemisBarrTest()
