from scipy.stats import gamma


def generate_gamma(size, alfa=0, beta=1):
    scale = 1 / beta
    return gamma.rvs(a=alfa, size=size, scale=scale)
