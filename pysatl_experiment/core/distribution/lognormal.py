import math

import numpy as np
from scipy.stats import lognorm


def generate_lognorm(size, mu=0, s=1):
    scale = math.exp(mu)
    return lognorm.rvs(s=np.sqrt(s), size=size, scale=scale)
