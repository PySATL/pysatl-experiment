from pysatl_experiment.core.distribution import norm, weibull
from pysatl_experiment.experiment.hypothesis.model import AbstractGofHypothesis, AbstractHypothesis


class NormalGofHypothesis(AbstractGofHypothesis):
    @staticmethod
    def code() -> str:
        return "NORMAL_GOF_HYPOTHESIS"

    def __init__(self, mean=0, var=1):
        self.mean = mean
        self.var = var

    def generate(self, size, **kwargs):
        return norm.generate_norm(size, self.mean, self.var)


class WeibullGofHypothesis(AbstractGofHypothesis):
    @staticmethod
    def code() -> str:
        return "WEIBULL_GOF_HYPOTHESIS"

    def __init__(self, a=1, k=5):
        self.a = a
        self.k = k

    def generate(self, size, **kwargs):
        return weibull.generate_weibull(size, self.a, self.k)


class UniformityHypothesis(AbstractHypothesis):
    @staticmethod
    def code() -> str:
        return "UNIFORMITY_HYPOTHESIS"
