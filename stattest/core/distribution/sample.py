import numpy as np
from scipy.stats import moment as scipy_moment


def moment(a, mom=1, center=None):
    scipy_moment(a=a, moment=mom, center=center)


def central_moment(a, mom=1):
    return scipy_moment(a=a, moment=mom, center=np.mean(a, axis=0))
