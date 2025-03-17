from stattest.core.distribution import norm, weibull, expon
from stattest.experiment.hypothesis.model import AbstractHypothesis


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

class ExponentialHypothesis(AbstractHypothesis):
    def __init__(self, lam=1):
        self.lam = lam

    def generate(self, size, **kwargs):
        return expon.generate_expon(size, self.lam)
