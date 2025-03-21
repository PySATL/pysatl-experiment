from scipy.stats import chi2


def generate_chi2(size, df=2):
    return chi2.rvs(df=df, size=size)
