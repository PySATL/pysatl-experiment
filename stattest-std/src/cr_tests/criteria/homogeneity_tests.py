from typing import override

from stattest.src.cr_tests.criteria.abstract_test import AbstractTest


class HomogeneityTest(AbstractTest):
    @staticmethod
    @override
    def code():
        return '_hmg'
