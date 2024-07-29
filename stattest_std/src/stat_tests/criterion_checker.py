from stattest_std.src.stat_tests.abstract_test import AbstractTest


class CriterionLauncher:
    def __init__(self, criterion: AbstractTest):
        self.criterion = criterion

    def check(self, sample, alpha):
        return self.criterion.test(sample, alpha)
        # TODO: different params problem - should check in criteria!!!

# TODO: remove from directory


'''   
 def get_sample(self):
        return self_sample()
'''
