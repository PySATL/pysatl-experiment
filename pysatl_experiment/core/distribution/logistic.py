from scipy.stats import logistic


def generate_logistic(size, t=0, s=1):
    return logistic.rvs(size=size, loc=t, scale=s)
