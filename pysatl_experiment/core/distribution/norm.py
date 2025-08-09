import numpy as np
from scipy.stats import norm


def generate_norm(size, mean=0, var=1):
    return norm.rvs(size=size, loc=mean, scale=np.sqrt(var))


def cdf_norm(rvs, mean=0, var=1):
    return norm.cdf(rvs, loc=mean, scale=np.sqrt(var))


def pdf_norm(rvs, mean=0, var=1):
    return norm.pdf(rvs, loc=mean, scale=np.sqrt(var))
