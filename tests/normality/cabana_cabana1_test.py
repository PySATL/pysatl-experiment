import pytest as pytest

from stattest.test.normal import CabanaCabana1NormalityTest
from tests.normality.abstract_normality_test_case import AbstractNormalityTestCase


@pytest.mark.parametrize(
    ("data", "result"),
    [
        (
            [
                -0.33234073,
                -1.73762000,
                -0.08110214,
                1.13414679,
                0.09228884,
                -0.69521329,
                0.10573062,
            ],
            0.2897665,
        ),
        (
            [
                0.99880346,
                -0.07557944,
                0.25368407,
                -1.20830967,
                -0.15914329,
                0.16900984,
                0.99395022,
                -0.28167969,
                0.11683112,
                0.68954236,
            ],
            0.5265257,
        ),
    ],
)
class TestCaseCabanaCabana1NormalityTest(AbstractNormalityTestCase):
    @pytest.fixture
    def statistic_test(self):
        return CabanaCabana1NormalityTest()
