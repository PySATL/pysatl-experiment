import numpy as np
from scipy.stats import truncnorm


def generate_truncnorm(size, mean=0, var=1, a=-10, b=10):
    return truncnorm.rvs(a=a, b=b, size=size, loc=mean, scale=np.sqrt(var))
