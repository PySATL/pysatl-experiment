import pytest as pytest

from stattest.test.normal import DesgagneLafayeNormalityTest
from tests.normality.abstract_normality_test_case import \
    AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        ([0.7258605, -1.0666939, -1.3391837,  0.1826556, -0.9695532,  0.5618815, -1.5228123], 5.583199),
        ([-0.59336721, 1.31220820, -0.82065801, -1.68778329, 1.96735245, -0.43180098, -0.63682878, -1.34366222,
          -0.03375564, 1.30610658], 0.8639117)
    ]
)
class TestDesgagneLafayeTest(AbstractNormalityTestCase):

    @pytest.fixture
    def statistic_test(self):
        return DesgagneLafayeNormalityTest()
