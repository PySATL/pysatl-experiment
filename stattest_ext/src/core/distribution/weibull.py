from scipy.stats import weibull_min


def generate_weibull(size, lam=0, k=1):
    return weibull_min.rvs(c=k, size=size, scale=lam)
