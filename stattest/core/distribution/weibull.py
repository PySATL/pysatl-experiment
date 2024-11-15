from scipy.stats import exponweib


def generate_weibull(size, l=1, k=5):
    return exponweib.rvs(a=l, c=k, size=size)


def generate_weibull_cdf(rvs, l=1, k=5):
    return exponweib.cdf(rvs, a=l, c=k)


def generate_weibull_logcdf(rvs, l=1, k=5):
    return exponweib.logcdf(rvs, a=l, c=k)


def generate_weibull_logsf(rvs, l=1, k=5):
    return exponweib.logsf(rvs, a=l, c=k)
