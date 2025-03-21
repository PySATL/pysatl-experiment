from pysatl_experiment.core.distribution import norm, weibull
from pysatl_experiment.experiment.hypothesis.model import AbstractHypothesis


class NormalHypothesis(AbstractHypothesis):
    def __init__(self, mean=0, var=1):
        self.mean = mean
        self.var = var

    def generate(self, size, **kwargs):
        return norm.generate_norm(size, self.mean, self.var)


class WeibullHypothesis(AbstractHypothesis):
    def __init__(self, a=1, k=5):
        self.a = a
        self.k = k

    def generate(self, size, **kwargs):
        return weibull.generate_weibull(size, self.a, self.k)
