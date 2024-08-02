from typing import override

from stattest_std.src.stat_tests.abstract_test import AbstractTest


class IndependenceTest(AbstractTest):
    @staticmethod
    @override
    def code():
        return '_ind'


class ChiSquareTest(IndependenceTest):

    @staticmethod
    @override
    def code():
        return 'CHI2' + super(ChiSquareTest, ChiSquareTest).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        print("Not implemented")  # TODO: stub from normality tests (should be two params)
        """
        rvs = np.sort(rvs)

        f_obs = np.asanyarray(rvs)
        f_obs_float = f_obs.astype(np.float64)
        f_exp = pdf_norm(rvs)
        scipy_stats.chi2_contingency()
        terms = (f_obs_float - f_exp) ** 2 / f_exp
        return terms.sum(axis=0)
        """
