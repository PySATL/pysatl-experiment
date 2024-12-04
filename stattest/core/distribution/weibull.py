from scipy.stats import exponweib


def generate_weibull(size, a=1, k=5):
    return exponweib.rvs(a=a, c=k, size=size)


def generate_weibull_cdf(rvs, a=1, k=5):
    return exponweib.cdf(rvs, a=a, c=k)


def generate_weibull_logcdf(rvs, a=1, k=5):
    return exponweib.logcdf(rvs, a=a, c=k)


def generate_weibull_logsf(rvs, a=1, k=5):
    return exponweib.logsf(rvs, a=a, c=k)
