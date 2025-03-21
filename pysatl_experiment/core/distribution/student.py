from scipy.stats import t


def generate_t(size, df=2):
    return t.rvs(df=df, size=size)
