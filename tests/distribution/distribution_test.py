import math

import numpy as np
import pytest

from pysatl_experiment.core.distribution.beta import generate_beta
from pysatl_experiment.core.distribution.cauchy import generate_cauchy
from pysatl_experiment.core.distribution.chi2 import generate_chi2
from pysatl_experiment.core.distribution.expon import generate_expon
from pysatl_experiment.core.distribution.gamma import generate_gamma
from pysatl_experiment.core.distribution.gumbel import generate_gumbel
from pysatl_experiment.core.distribution.laplace import generate_laplace
from pysatl_experiment.core.distribution.lo_con_norm import generate_lo_con_norm
from pysatl_experiment.core.distribution.logistic import generate_logistic
from pysatl_experiment.core.distribution.lognormal import generate_lognorm
from pysatl_experiment.core.distribution.mix_con_norm import generate_mix_con_norm
from pysatl_experiment.core.distribution.norm import generate_norm
from pysatl_experiment.core.distribution.scale_con_norm import generate_scale_con_norm
from pysatl_experiment.core.distribution.student import generate_t
from pysatl_experiment.core.distribution.truncnormal import generate_truncnorm
from pysatl_experiment.core.distribution.tukey import generate_tukey
from pysatl_experiment.core.distribution.uniform import generate_uniform
from pysatl_experiment.core.distribution.weibull import generate_weibull


@pytest.mark.skip(reason="no way of currently testing this")
class TestDistribution:
    size = 10000

    @pytest.mark.parametrize(
        ("mean", "a", "b"),
        [
            (0.5, 0.0, 1.0),
            (0, -1.0, 1.0),
            (3, 1.0, 5.0),
        ],
    )
    def test_generate_uniform(self, mean, a, b):
        uniform = generate_uniform(self.size / 10, a=a, b=b)
        e_mean = np.mean(uniform)
        assert e_mean == pytest.approx(mean, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "a", "b"),
        [
            (0, 1, 0, 1),
            (-1, 3, -1, 3),
            (10, 5, 10, 5),
        ],
    )
    def test_generate_norm(self, mean, var, a, b):
        rvs = generate_norm(self.size, mean=a, var=b)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "a", "b"),
        [
            (0.2, 0.026666, 1, 4),
            (0.5, 0.125, 0.5, 0.5),
        ],
    )
    def test_generate_beta(self, mean, var, a, b):
        rvs = generate_beta(self.size, a=a, b=b)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "t", "s"),
        [
            (0, 0, 0.1),
        ],
    )
    def test_generate_cauchy(self, mean, t, s):
        rvs = generate_cauchy(self.size, t=t, s=s)
        e_mean = np.mean(rvs)
        # cauchy has no mean
        assert e_mean == pytest.approx(mean, abs=1)

    @pytest.mark.parametrize(
        ("mean", "var", "lam"),
        [
            (1, 1, 1),
            (0.25, 1 / 16, 4),
        ],
    )
    def test_generate_expon(self, mean, var, lam):
        rvs = generate_expon(self.size, lam)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "alfa", "beta"),
        [
            (1, 1, 1, 1),
            (0.8, 0.16, 4, 5),
        ],
    )
    def test_generate_gamma(self, mean, var, alfa, beta):
        rvs = generate_gamma(self.size, alfa=alfa, beta=beta)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "mu", "beta"),
        [
            (1 + 1 * 0.57721566, math.pi**2 / 6, 1, 1),
            (4 + 3 * 0.57721566, math.pi**2 * 9 / 6, 4, 3),
        ],
    )
    def test_generate_gumbel(self, mean, var, mu, beta):
        rvs = generate_gumbel(self.size, mu=mu, beta=beta)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.3)
        assert e_var == pytest.approx(var, abs=0.3)

    @pytest.mark.parametrize(
        ("mean", "var", "t", "s"),
        [
            (1, 2, 1, 1),
            (4, 2 * 4, 4, 2),
        ],
    )
    def test_generate_laplace(self, mean, var, t, s):
        rvs = generate_laplace(self.size, t=t, s=s)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "t", "s"),
        [
            (1, math.pi**2 / 3, 1, 1),
            (4, math.pi**2 * 4 / 3, 4, 2),
        ],
    )
    def test_generate_logistic(self, mean, var, t, s):
        rvs = generate_logistic(10000, t=t, s=s)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "mu", "s"),
        [
            (math.exp(0.5), (math.exp(1) - 1) * math.exp(1), 0, 1),
            (math.exp(1.5), (math.exp(1) - 1) * math.exp(3), 1, 1),
            (math.exp(0.125), (math.exp(0.25) - 1) * math.exp(0.25), 0, 0.25),
            (math.exp(1.125), (math.exp(0.25) - 1) * math.exp(2.25), 1, 0.25),
        ],
    )
    def test_generate_lognorm(self, mean, var, mu, s):
        rvs = generate_lognorm(self.size, mu=mu, s=s)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.5)
        assert e_var == pytest.approx(var, abs=1.5)

    @pytest.mark.parametrize(
        ("mean", "var", "df"),
        [
            (0, 3, 3),
            (0, 2, 4),
        ],
    )
    def test_generate_t(self, mean, var, df):
        rvs = generate_t(self.size, df=df)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.5)

    @pytest.mark.parametrize(
        ("mean", "var", "df"),
        [
            (1, 2, 1),
            (2, 4, 2),
            (4, 8, 4),
        ],
    )
    def test_generate_chi2(self, mean, var, df):
        rvs = generate_chi2(self.size, df=df)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.5)

    @pytest.mark.parametrize(
        ("mean", "var", "m", "v", "a", "b"),
        [
            (0, 1, 0, 1, -10, 10),
            (5, 2, 5, 2, -5, 15),
        ],
    )
    def test_generate_truncnorm(self, mean, var, m, v, a, b):
        rvs = generate_truncnorm(self.size, mean=m, var=v, a=a, b=b)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "lam"),
        [
            (0, 1 / 12, 2),
            (0, math.pi**2 / 3, 0),
        ],
    )
    def test_generate_tukey(self, mean, var, lam):
        rvs = generate_tukey(self.size, lam=lam)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.2)

    @pytest.mark.parametrize(
        ("mean", "var", "k", "lam"),
        [
            (1, 1, 1, 1),
            (4, 16, 1, 4),
            (0.9064, 0.0646614750404533, 4, 1),
        ],
    )
    def test_generate_weibull(self, mean, var, k, lam):
        rvs = generate_weibull(self.size, k=k, lam=lam)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.3)

    @pytest.mark.parametrize(
        ("mean", "var", "p", "a"),
        [
            (0, 1, 0.5, 0),
            (35, 1, 0.7, 50),
        ],
    )
    def test_generate_lo_con_norm(self, mean, var, p, a):
        rvs = generate_lo_con_norm(self.size, p=p, a=a)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.3)

    @pytest.mark.parametrize(
        ("mean", "var", "p", "b"),
        [
            (0, 1, 0.5, 1),
            (0, 3, 0.7, 2),
        ],
    )
    def test_generate_scale_con_norm(self, mean, var, p, b):
        rvs = generate_scale_con_norm(self.size, p=p, b=b)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.3)

    @pytest.mark.parametrize(
        ("mean", "var", "p", "a", "b"),
        [
            (0, 1, 0.5, 0, 1),
            (35, 3, 0.7, 50, 2),
        ],
    )
    def test_generate_mix_con_norm(self, mean, var, p, a, b):
        rvs = generate_mix_con_norm(self.size, p=p, a=a, b=b)
        e_mean = np.mean(rvs)
        e_var = np.var(rvs)
        assert e_mean == pytest.approx(mean, abs=0.2)
        assert e_var == pytest.approx(var, abs=0.3)
