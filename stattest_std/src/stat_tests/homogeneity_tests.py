from typing import override

from stattest_std.src.stat_tests.abstract_test import AbstractTest


class HomogeneityTest(AbstractTest):
    @staticmethod
    @override
    def code():
        return '_hmg'
