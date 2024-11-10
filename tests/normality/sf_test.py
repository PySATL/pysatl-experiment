import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/sf_test.py
from stattest_std.src.stat_tests.normality_tests import SFTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import SFTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/sf_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-1.5461357, 0.8049704, -1.2676556, 0.1912453, 1.4391551, 0.5352138, -1.6212611, 0.1015035, -0.2571793,
          0.8756286], 0.93569),
    ],
)
class TestCaseSFNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return SFTest()
