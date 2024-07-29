import csv
import os

import stattest.execution.utils as utils
from stattest.execution.utils import build_rvs_file_name
from stattest.test.generator import AbstractRVSGenerator, BetaRVSGenerator
import pandas as pd


def generate_rvs_data(rvs_generator: AbstractRVSGenerator, size, count=1_000):
    """
    Generate data rvs

    :param rvs_generator: generator to generate rvs data
    :param size: size of rvs vector
    :param count: rvs count
    :return: Data Frame, where rows is rvs
    """
    # df = pd.DataFrame(columns=[str(x) for x in range(1, size + 1)], index=range(1, size + 1))
    result = []
    for i in range(count):
        # df.loc[i] = list(rvs_generator.generate(size))
        result.append(rvs_generator.generate(size))
    # return df
    return result


def prepare_one_size_rvs_data(rvs_generators: [AbstractRVSGenerator], size, count=1_000, path='data'):
    """
    Generate data rvs and save it to files {generator_code}.csv

    :param size: size of rvs
    :param path: path to folder where data will be persisted
    :param rvs_generators: generators list to generate rvs data
    :param count: rvs count
    """

    for generator in rvs_generators:
        data = generate_rvs_data(generator, size, count)
        file_path = os.path.join(path, build_rvs_file_name(generator.code(), size) + '.csv')
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=utils.CSV_SEPARATOR, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(data)
        # df.to_csv(file_path, sep=utils.CSV_SEPARATOR, encoding=utils.CSV_ENCODING, header=False, index=False)


def prepare_rvs_data(rvs_generators: [AbstractRVSGenerator], sizes: [], count=1_000, path='data'):
    """
    Generate data rvs and save it to files {generator_code}.csv

    :param sizes: sizes of rvs
    :param path: path to folder where data will be persisted
    :param rvs_generators: generators list to generate rvs data
    :param count: rvs count
    """

    if not os.path.exists(path):
        os.makedirs(path)

    for size in sizes:
        prepare_one_size_rvs_data(rvs_generators, size, count, path)


"""if __name__ == '__main__':
    sizes = [30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 1000]
    prepare_rvs_data([BetaRVSGenerator(a=0.5, b=0.5)], sizes)
    """
