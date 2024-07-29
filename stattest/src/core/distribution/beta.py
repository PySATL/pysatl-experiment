from scipy.stats import beta


def generate_beta(size, a=0.0, b=1.0):
    return beta.rvs(a=a, b=b, size=size)
