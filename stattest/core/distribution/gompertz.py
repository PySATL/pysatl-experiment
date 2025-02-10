from scipy.stats import gompertz


def generate_gompertz(size, eta=0, b=1):
    return gompertz.rvs(eta, size=size, scale=b)
