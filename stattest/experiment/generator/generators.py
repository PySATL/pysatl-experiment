from typing_extensions import override

from stattest.core.distribution.beta import generate_beta
from stattest.core.distribution.cauchy import generate_cauchy
from stattest.core.distribution.chi2 import generate_chi2
from stattest.core.distribution.expon import generate_expon
from stattest.core.distribution.gamma import generate_gamma
from stattest.core.distribution.gompertz import generate_gompertz
from stattest.core.distribution.gumbel import generate_gumbel
from stattest.core.distribution.invgauss import generate_invgauss
from stattest.core.distribution.laplace import generate_laplace
from stattest.core.distribution.lo_con_norm import generate_lo_con_norm
from stattest.core.distribution.logistic import generate_logistic
from stattest.core.distribution.lognormal import generate_lognorm
from stattest.core.distribution.mix_con_norm import generate_mix_con_norm
from stattest.core.distribution.norm import generate_norm
from stattest.core.distribution.rice import generate_rice
from stattest.core.distribution.scale_con_norm import generate_scale_con_norm
from stattest.core.distribution.student import generate_t
from stattest.core.distribution.truncnormal import generate_truncnorm
from stattest.core.distribution.tukey import generate_tukey
from stattest.core.distribution.weibull import generate_weibull
from stattest.experiment.generator.model import AbstractRVSGenerator


class BetaRVSGenerator(AbstractRVSGenerator):
    def __init__(self, a, b, **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.b = b

    @override
    def code(self):
        return super()._convert_to_code(["beta", self.a, self.b])

    @override
    def generate(self, size):
        return generate_beta(size=size, a=self.a, b=self.b)


class CauchyRVSGenerator(AbstractRVSGenerator):
    def __init__(self, t, s, **kwargs):
        super().__init__(**kwargs)
        self.t = t
        self.s = s

    @override
    def code(self):
        return super()._convert_to_code(["cauchy", self.t, self.s])

    @override
    def generate(self, size):
        return generate_cauchy(size=size, t=self.t, s=self.s)


class LaplaceRVSGenerator(AbstractRVSGenerator):
    def __init__(self, t, s, **kwargs):
        super().__init__(**kwargs)
        self.t = t
        self.s = s

    @override
    def code(self):
        return super()._convert_to_code(["laplace", self.t, self.s])

    @override
    def generate(self, size):
        return generate_laplace(size=size, t=self.t, s=self.s)


class LogisticRVSGenerator(AbstractRVSGenerator):
    def __init__(self, t, s, **kwargs):
        super().__init__(**kwargs)
        self.t = t
        self.s = s

    @override
    def code(self):
        return super()._convert_to_code(["logistic", self.t, self.s])

    @override
    def generate(self, size):
        return generate_logistic(size=size, t=self.t, s=self.s)


class TRVSGenerator(AbstractRVSGenerator):
    def __init__(self, df, **kwargs):
        super().__init__(**kwargs)
        self.df = df

    @override
    def code(self):
        return super()._convert_to_code(["student", self.df])

    @override
    def generate(self, size):
        return generate_t(size=size, df=self.df)


class TukeyRVSGenerator(AbstractRVSGenerator):
    def __init__(self, lam, **kwargs):
        super().__init__(**kwargs)
        self.lam = lam

    @override
    def code(self):
        return super()._convert_to_code(["tukey", self.lam])

    @override
    def generate(self, size):
        return generate_tukey(size=size, lam=self.lam)


class LognormGenerator(AbstractRVSGenerator):
    def __init__(self, s=1, mu=0, **kwargs):
        super().__init__(**kwargs)
        self.s = s
        self.mu = mu

    @override
    def code(self):
        return super()._convert_to_code(["lognorm", self.s, self.mu])

    @override
    def generate(self, size):
        return generate_lognorm(size=size, s=self.s, mu=self.mu)


class GammaGenerator(AbstractRVSGenerator):
    def __init__(self, alfa=1, beta=0, **kwargs):
        super().__init__(**kwargs)
        self.alfa = alfa
        self.beta = beta

    @override
    def code(self):
        return super()._convert_to_code(["gamma", self.alfa, self.beta])

    @override
    def generate(self, size):
        return generate_gamma(size=size, alfa=self.alfa, beta=self.beta)


class TruncnormGenerator(AbstractRVSGenerator):
    def __init__(self, mean=0, var=1, a=-10, b=10, **kwargs):
        super().__init__(**kwargs)
        self.mean = mean
        self.var = var
        self.a = a
        self.b = b

    @override
    def code(self):
        return super()._convert_to_code(["truncnorm", self.mean, self.var, self.a, self.b])

    @override
    def generate(self, size):
        return generate_truncnorm(size=size, mean=self.mean, var=self.var, a=self.a, b=self.b)


class Chi2Generator(AbstractRVSGenerator):
    def __init__(self, df=2, **kwargs):
        super().__init__(**kwargs)
        self.df = df

    @override
    def code(self):
        return super()._convert_to_code(["chi2", self.df])

    @override
    def generate(self, size):
        return generate_chi2(size=size, df=self.df)


class GumbelGenerator(AbstractRVSGenerator):
    def __init__(self, mu=0, beta=1, **kwargs):
        super().__init__(**kwargs)
        self.mu = mu
        self.beta = beta

    @override
    def code(self):
        return super()._convert_to_code(["gumbel", self.mu, self.beta])

    @override
    def generate(self, size):
        return generate_gumbel(size=size, mu=self.mu, beta=self.beta)


class WeibullGenerator(AbstractRVSGenerator):
    def __init__(self, a=1, k=5, **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.k = k

    @override
    def code(self):
        return super()._convert_to_code(["weibull", self.a, self.k])

    @override
    def generate(self, size):
        return generate_weibull(size=size, a=self.a, k=self.k)


class LoConNormGenerator(AbstractRVSGenerator):
    def __init__(self, p=0.5, a=0, **kwargs):
        super().__init__(**kwargs)
        self.p = p
        self.a = a

    @override
    def code(self):
        return super()._convert_to_code(["lo_con_norm", self.p, self.a])

    @override
    def generate(self, size):
        return generate_lo_con_norm(size=size, p=self.p, a=self.a)


class ScConNormGenerator(AbstractRVSGenerator):
    def __init__(self, p=0.5, b=1, **kwargs):
        super().__init__(**kwargs)
        self.p = p
        self.b = b

    @override
    def code(self):
        return super()._convert_to_code(["scale_con_norm", self.p, self.b])

    @override
    def generate(self, size):
        return generate_scale_con_norm(size=size, p=self.p, b=self.b)


class MixConNormGenerator(AbstractRVSGenerator):
    def __init__(self, p=0.5, a=0, b=1, **kwargs):
        super().__init__(**kwargs)
        self.p = p
        self.a = a
        self.b = b

    @override
    def code(self):
        return super()._convert_to_code(["mix_con_norm", self.p, self.a, self.b])

    @override
    def generate(self, size):
        return generate_mix_con_norm(size=size, p=self.p, a=self.a, b=self.b)


class ExponentialGenerator(AbstractRVSGenerator):
    def __init__(self, lam=0.5, **kwargs):
        super().__init__(**kwargs)
        self.lam = lam

    @override
    def code(self):
        return super()._convert_to_code(["exponential", self.lam])

    @override
    def generate(self, size):
        return generate_expon(size=size, lam=self.lam)


class InvGaussGenerator(AbstractRVSGenerator):
    def __init__(self, mu=0, lam=1, **kwargs):
        super().__init__(**kwargs)
        self.mu = mu
        self.lam = lam

    @override
    def code(self):
        return super()._convert_to_code(["invgauss", self.mu, self.lam])

    @override
    def generate(self, size):
        return generate_invgauss(size=size, mu=self.mu, lam=self.lam)


class RiceGenerator(AbstractRVSGenerator):
    def __init__(self, nu=0, sigma=1, **kwargs):
        super().__init__(**kwargs)
        self.nu = nu
        self.sigma = sigma

    @override
    def code(self):
        return super()._convert_to_code(["rice", self.nu, self.sigma])

    @override
    def generate(self, size):
        return generate_rice(size=size, nu=self.nu, sigma=self.sigma)


class GompertzGenerator(AbstractRVSGenerator):
    def __init__(self, eta=0, b=1, **kwargs):
        super().__init__(**kwargs)
        self.eta = eta
        self.b = b

    @override
    def code(self):
        return super()._convert_to_code(["gompertz", self.eta, self.b])

    @override
    def generate(self, size):
        return generate_gompertz(size=size, eta=self.eta, b=self.b)

class NormalRVSGenerator(AbstractRVSGenerator):
    def __init__(self, mean, var, **kwargs):
        super().__init__(**kwargs)
        self.mean = mean
        self.var = var

    @override
    def code(self):
        return super()._convert_to_code(["norm", self.mean, self.var])

    @override
    def generate(self, size):
        return generate_norm(size, mean=self.mean, var=self.var)
