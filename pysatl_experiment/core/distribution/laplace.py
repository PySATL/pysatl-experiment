from scipy.stats import laplace


def generate_laplace(size, t=0, s=1):
    return laplace.rvs(size=size, loc=t, scale=s)
