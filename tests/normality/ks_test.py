import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/ks_test.py
from stattest_std.src.stat_tests.normality_tests import KSTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import KSNormalityTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/ks_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Normal with mean = 0, variance = 1
        ([0.38323312, -1.10386561, 0.75226465, -2.23024566, -0.27247827, 0.95926434, 0.42329541, -0.11820711,
          0.90892169, -0.29045373], 0.18573457378941832),
        # Normal with mean = 11, variance = 1
        ([-0.46869863, -0.22452687, -1.7674444, -0.727139, 1.09089112, -0.01319041, 0.38578004, 1.47354665,
          0.95253258, -1.17323879], 0.12958652448618313),
        # Normal with mean = 0, variance = 5
        ([-0.46869863, -0.22452687, -1.7674444, -0.727139, 1.09089112, -0.01319041, 0.38578004, 1.47354665,
          0.95253258, -1.17323879], 0.12958652448618313),
        # Normal with mean = 11, variance = 5
        ([-0.46869863, -0.22452687, -1.7674444, -0.727139, 1.09089112, -0.01319041, 0.38578004, 1.47354665,
          0.95253258, -1.17323879], 0.12958652448618313)
    ],
)
class TestCaseKSNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return KSNormalityTest()
