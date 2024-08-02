from typing import override

from stattest_ext.src.core.distribution import expon
from stattest_ext.src.tests_generators.stat_gen_goodness_test import StatGenGoodnessOfFitTest
from stattest_std.src.stat_tests.exponentiality_tests import ExponentialityTest


class StatGenExponentialityTest(StatGenGoodnessOfFitTest):
    def __init__(self, criterion: ExponentialityTest):
        super().__init__(criterion)
        self.criterion = criterion

    @override
    def generate(self, size):
        return expon.generate_expon(size, self.criterion.lam)
