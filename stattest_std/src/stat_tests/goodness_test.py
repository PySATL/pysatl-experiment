from typing import override

from stattest_std.src.stat_tests.abstract_test import AbstractTest


class GoodnessOfFitTest(AbstractTest):
    @staticmethod
    @override
    def code():
        raise "Should be implemented in sub-class"
