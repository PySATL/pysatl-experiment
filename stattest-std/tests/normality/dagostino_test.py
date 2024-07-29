import pytest as pytest

from stattest.src.cr_tests.criteria.normality_tests import DagostinoTest
from stattest.tests.normality.abstract_test_case import AbstractTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([-0.4419019, -0.3962638, -0.9919951, -1.7636001,  1.0433300, -0.6375415,  1.2467400], -0.7907805),
        ([0.67775366, -0.07238245,  1.87603589,  0.46277364,  1.10585543, -0.95274655,
          -1.47549650,  0.42478574,  0.91713384,  0.24491208], -0.7608445),
    ],
)
class TestCaseDagostinoTest(AbstractTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DagostinoTest()
