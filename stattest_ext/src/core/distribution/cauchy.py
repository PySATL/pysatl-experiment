from scipy.stats import cauchy


def generate_cauchy(size, t=0.5, s=0.5):
    return cauchy.rvs(size=size, loc=t, scale=s)
