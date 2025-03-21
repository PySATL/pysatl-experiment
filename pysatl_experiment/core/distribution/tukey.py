from scipy.stats import tukeylambda


def generate_tukey(size, lam=2):
    return tukeylambda.rvs(lam, size=size)
