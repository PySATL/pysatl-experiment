from typing import override

from stattest.src.cr_tests.criteria.abstract_test import AbstractTest


class GoodnessOfFitTest(AbstractTest):
    @staticmethod
    @override
    def code():
        raise "Should be implemented in sub-class"
