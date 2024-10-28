from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.core.distribution import norm
from stattest.core.distribution import weibull


class NormalHypothesis(AbstractHypothesis):
    def __init__(self, mean=0, var=1):
        self.mean = mean
        self.var = var

    def generate(self, size, **kwargs):
        return norm.generate_norm(size, self.mean, self.var)


class WeibullHypothesis(AbstractHypothesis):
    def __init__(self, l=1, k=5):
        self.l = l
        self.k = k

    def generate(self, size, **kwargs):
        return weibull.generate_weibull(size, self.l, self.k)
