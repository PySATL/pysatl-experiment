from scipy.stats import rice


def generate_rice(size, nu=0, sigma=1):
    return rice.rvs(nu, size=size, scale=sigma)
