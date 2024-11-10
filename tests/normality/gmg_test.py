import pytest as pytest

<<<<<<<< HEAD:stattest_std/tests/normality/gmg_test.py
from stattest_std.src.stat_tests.normality_tests import GMGTest
from stattest_std.tests.normality.abstract_normality_test_case import AbstractNormalityTestCase
========
from stattest.test.normal import GMGTest
from tests.AbstractTestCase import AbstractTestCase
>>>>>>>> architecture:tests/normality/gmg_test.py


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-0.01686868,  1.98378809,  1.34831025,  0.38120500, -0.35364982, -0.65345851,  0.05968902], 1.033118),
        ([1.00488088, -1.71519143,  0.48269944, -0.10380093, -0.02961192, -0.42891128,
          0.07543129, -0.03098110, -0.72435341, -0.90046224], 1.066354),
    ],
)
class TestCaseGMGNormalityTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return GMGTest()
