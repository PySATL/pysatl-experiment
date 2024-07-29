import json
import os
from os.path import exists
import numpy as np
from stattest.ext_package.experiment import Distribution


def generate_samples(dist_type: Distribution = None,
                     number: int = None,
                     start_size: int = None,
                     final_size: int = None,
                     step: int = None,
                     path: str = None):
    """
    Generates samples based on parameters.

    Parameters
    ----------
    dist_type : Distribution
        Enum value representing distribution type.
    number : int
        Number of samples of each size.
    start_size : int
        Start size of the samples.
    final_size : int
        Final size of the samples.
    step : int
        Step of the iteration.
    path : str
        Path to save JSON file to.

    Returns
    -------
    True
    """
    path = path if path is not None else os.getcwd()

    all_types = dist_type is None

    filename = f"{'all' if all_types else dist_type.value}_{number}_{start_size}_{final_size}_{step}"
    if exists(f"{path}/{filename}.json"):
        raise FileExistsError("Such samples already exist")

    samples_by_size = {
            size: [None for _ in range(number)]
            for size in range(start_size, final_size + 1, step)
        }
    samples = {
        type_.value: samples_by_size for type_ in Distribution
        } if all_types else {dist_type.value: samples_by_size}

    for size in range(start_size, final_size + 1, step):
        for i in range(number):
            if all_types or dist_type is Distribution.no_type:
                sample = np.random.random_sample(size=size)
                samples[dist_type.value][size][i] = list(sample)

            if all_types or dist_type is Distribution.normal:
                sample = np.random.normal(loc=0, scale=1, size=size)
                samples[dist_type.value][size][i] = list(sample)

            if all_types or dist_type is Distribution.exponential:
                sample = np.random.exponential(scale=1, size=size)
                samples[dist_type.value][size][i] = list(sample)

    save_file = open(f"{path}/{filename}.json", "w")
    json.dump(samples, save_file, indent=4)
    save_file.close()

    return True
