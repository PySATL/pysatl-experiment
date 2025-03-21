from scipy.stats import invgauss


def generate_invgauss(size, mu=0, lam=1):
    return invgauss.rvs(mu, size=size, scale=lam)
