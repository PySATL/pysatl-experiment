from typing import override

from stattest_ext.src.core.distribution import norm
from stattest_ext.src.tests_generators.stat_gen_goodness_test import StatGenGoodnessOfFitTest
from stattest_std.src.stat_tests.normality_tests import NormalityTest


class StatGenNormalityTest(StatGenGoodnessOfFitTest, NormalityTest):
    def __init__(self, criterion: NormalityTest):
        super().__init__()
        self.criterion = criterion

    @override
    def generate(self, size):
        return norm.generate_norm(size, self.criterion.mean, self.criterion.var)
