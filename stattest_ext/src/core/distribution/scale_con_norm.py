import numpy as np
from scipy.stats import norm


def generate_scale_con_norm(size, p=0.5, b=0) -> [float]:
    """
     Consisting of randomly selected observations with probability 1 − p drawn from a standard
     normal distribution and with probability p drawn from a normal distribution with mean 0 and
     standard deviation b.

    :param size: generated rvs size
    :param p: probability
    :param b: standard deviation
    :return:
    """

    result = []
    for i in range(size):
        choice = np.random.choice(np.arange(2), p=[p, 1 - p])
        if choice == 0:
            item = norm.rvs(size=1, scale=b)
        else:
            item = norm.rvs(size=1)
        result.append(item)

    return np.concatenate(result, axis=0)
