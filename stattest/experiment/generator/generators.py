from stattest.core.distribution.beta import generate_beta
from stattest.core.distribution.cauchy import generate_cauchy
from stattest.core.distribution.chi2 import generate_chi2
from stattest.core.distribution.gamma import generate_gamma
from stattest.core.distribution.gumbel import generate_gumbel
from stattest.core.distribution.laplace import generate_laplace
from stattest.core.distribution.lo_con_norm import generate_lo_con_norm
from stattest.core.distribution.logistic import generate_logistic
from stattest.core.distribution.lognormal import generate_lognorm
from stattest.core.distribution.mix_con_norm import generate_mix_con_norm
from stattest.core.distribution.scale_con_norm import generate_scale_con_norm
from stattest.core.distribution.student import generate_t
from stattest.core.distribution.truncnormal import generate_truncnorm
from stattest.core.distribution.tukey import generate_tukey
from stattest.core.distribution.weibull import generate_weibull
from stattest.experiment.generator.model import AbstractRVSGenerator


class BetaRVSGenerator(AbstractRVSGenerator):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def code(self):
        return super()._convert_to_code(['beta', self.a, self.b])

    def generate(self, size):
        return generate_beta(size=size, a=self.a, b=self.b)


class CauchyRVSGenerator(AbstractRVSGenerator):
    def __init__(self, t, s):
        self.t = t
        self.s = s

    def code(self):
        return super()._convert_to_code(['cauchy', self.t, self.s])

    def generate(self, size):
        return generate_cauchy(size=size, t=self.t, s=self.s)


class LaplaceRVSGenerator(AbstractRVSGenerator):
    def __init__(self, t, s):
        self.t = t
        self.s = s

    def code(self):
        return super()._convert_to_code(['laplace', self.t, self.s])

    def generate(self, size):
        return generate_laplace(size=size, t=self.t, s=self.s)


class LogisticRVSGenerator(AbstractRVSGenerator):
    def __init__(self, t, s):
        self.t = t
        self.s = s

    def code(self):
        return super()._convert_to_code(['logistic', self.t, self.s])

    def generate(self, size):
        return generate_logistic(size=size, t=self.t, s=self.s)


class TRVSGenerator(AbstractRVSGenerator):
    def __init__(self, df):
        self.df = df

    def code(self):
        return super()._convert_to_code(['student', self.df])

    def generate(self, size):
        return generate_t(size=size, df=self.df)


class TukeyRVSGenerator(AbstractRVSGenerator):
    def __init__(self, lam):
        self.lam = lam

    def code(self):
        return super()._convert_to_code(['tukey', self.lam])

    def generate(self, size):
        return generate_tukey(size=size, lam=self.lam)


class LognormGenerator(AbstractRVSGenerator):
    def __init__(self, s=1, mu=0):
        self.s = s
        self.mu = mu

    def code(self):
        return super()._convert_to_code(['lognorm', self.s, self.mu])

    def generate(self, size):
        return generate_lognorm(size=size, s=self.s, mu=self.mu)


class GammaGenerator(AbstractRVSGenerator):
    def __init__(self, alfa=1, beta=0):
        self.alfa = alfa
        self.beta = beta

    def code(self):
        return super()._convert_to_code(['gamma', self.alfa, self.beta])

    def generate(self, size):
        return generate_gamma(size=size, alfa=self.alfa, beta=self.beta)


class TruncnormGenerator(AbstractRVSGenerator):
    def __init__(self, mean=0, var=1, a=-10, b=10):
        self.mean = mean
        self.var = var
        self.a = a
        self.b = b

    def code(self):
        return super()._convert_to_code(['truncnorm', self.mean, self.var, self.a, self.b])

    def generate(self, size):
        return generate_truncnorm(size=size, mean=self.mean, var=self.var, a=self.a, b=self.b)


class Chi2Generator(AbstractRVSGenerator):
    def __init__(self, df=2):
        self.df = df

    def code(self):
        return super()._convert_to_code(['chi2', self.df])

    def generate(self, size):
        return generate_chi2(size=size, df=self.df)


class GumbelGenerator(AbstractRVSGenerator):
    def __init__(self, mu=0, beta=1):
        self.mu = mu
        self.beta = beta

    def code(self):
        return super()._convert_to_code(['gumbel', self.mu, self.beta])

    def generate(self, size):
        return generate_gumbel(size=size, mu=self.mu, beta=self.beta)


class WeibullGenerator(AbstractRVSGenerator):
    def __init__(self, l=1, k=5):
        self.l = l
        self.k = k

    def code(self):
        return super()._convert_to_code(['weibull', self.l, self.k])

    def generate(self, size):
        return generate_weibull(size=size, l=self.l, k=self.k)


class LoConNormGenerator(AbstractRVSGenerator):
    def __init__(self, p=0.5, a=0):
        self.p = p
        self.a = a

    def code(self):
        return super()._convert_to_code(['lo_con_norm', self.p, self.a])

    def generate(self, size):
        return generate_lo_con_norm(size=size, p=self.p, a=self.a)


class ScConNormGenerator(AbstractRVSGenerator):
    def __init__(self, p=0.5, b=1):
        self.p = p
        self.b = b

    def code(self):
        return super()._convert_to_code(['scale_con_norm', self.p, self.b])

    def generate(self, size):
        return generate_scale_con_norm(size=size, p=self.p, b=self.b)


class MixConNormGenerator(AbstractRVSGenerator):
    def __init__(self, p=0.5, a=0, b=1):
        self.p = p
        self.a = a
        self.b = b

    def code(self):
        return super()._convert_to_code(['mix_con_norm', self.p, self.a, self.b])

    def generate(self, size):
        return generate_mix_con_norm(size=size, p=self.p, a=self.a, b=self.b)
