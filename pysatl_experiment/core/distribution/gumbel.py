from scipy.stats import gumbel_r


def generate_gumbel(size, mu=0, beta=1):
    return gumbel_r.rvs(size=size, loc=mu, scale=beta)
