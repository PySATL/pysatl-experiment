import numpy as np
from scipy.stats import norm


def generate_mix_con_norm(size, p=0.5, a=0, b=1) -> [float]:
    """
     Consisting of randomly selected observations with probability 1 − p drawn from a standard normal
     distribution and with probability p drawn from a normal distribution with mean a and standard deviation b.

    :param size: generated rvs size
    :param p: probability
    :param a: mean
    :param b: standard deviation
    :return:
    """

    result = []
    for i in range(size):
        choice = np.random.choice(np.arange(2), p=[p, 1 - p])
        if choice == 0:
            item = norm.rvs(size=1, loc=a, scale=b)
        else:
            item = norm.rvs(size=1)
        result.append(item)

    return np.concatenate(result, axis=0)
