from stattest.src.cr_tests.criteria.abstract_test import AbstractTest


class CriterionLauncher:
    def __init__(self, criterion: AbstractTest):
        self.criterion = criterion  # TODO: should be private??

    def check(self, sample, alpha):
        return self.criterion.test(sample, alpha)  # TODO: file inheritance (if we need it)
        # TODO: different params problem - should check in criteria!!!


'''   
 def get_sample(self):
        return self_sample()
'''
