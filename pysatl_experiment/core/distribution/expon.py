from scipy.stats import expon


def generate_expon(size, lam=1):  # TODO: refactor structure with inheritance??
    scale = 1 / lam
    return expon.rvs(size=size, scale=scale)


def cdf_expon(rvs, lam=1):
    scale = 1 / lam
    return expon.cdf(rvs, scale=scale)
