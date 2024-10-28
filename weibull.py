import numpy as np
from scipy import stats
from scipy.stats import kstest, anderson, weibull_min
import scipy.stats as scipy_stats

from stattest.core.distribution.weibull import generate_weibull
from stattest.test import KSWeibullTest, ADWeibullTest

if __name__ == '__main__':
    rvs = [0.98797153, 1.00042232, 1.02413383, 0.97340338, 0.91965021, 0.9918333,
           1.00816795, 0.96973347, 1.01931654, 1.01855464]  # generate_weibull(10, 1, 30)
    print(rvs)
    v2 = ADWeibullTest().execute_statistic(rvs)
    t = anderson(np.log(rvs), 'gumbel_l')
    print(np.exp(t.fit_result.params.loc), 1 / t.fit_result.params.scale)
    print(v2, t)

    '''speeds = np.linspace(0, 2.5, 1000)
    p = exponweib.pdf(speeds, a=1, c=1)

    plt.plot(speeds, p, 'b', linewidth=1)
    plt.fill_between(speeds, speeds * 0, p, facecolor='b', alpha=0.1)
    plt.ylabel('Probability Density')
    plt.show()'''
