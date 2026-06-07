"""Utility functions for loading generated samples from storage."""

from line_profiler import profile

from pysatl_experiment.persistence.model.random_values import IRandomValuesStorage, RandomValuesCountQuery


@profile
def get_sample_data_from_storage(
    generator_name: str,
    generator_parameters: list[float],
    sample_size: int,
    count: int,
    data_storage: IRandomValuesStorage,
) -> list[list[float]]:
    """
    Load generated samples from storage.

    Parameters
    ----------
    generator_name : str
        Name of the random value generator.
    generator_parameters : list[float]
        Generator parameters used during sample generation.
    sample_size : int
        Size of each generated sample.
    count : int
        Number of samples to load.
    data_storage : IRandomValuesStorage
        Storage backend containing generated random samples.

    Returns
    -------
    list[list[float]]
        Loaded samples.

    Raises
    ------
    ValueError
        If the storage contains fewer samples than requested.
    """
    data = []

    query = RandomValuesCountQuery(
        generator_name=generator_name,
        generator_parameters=generator_parameters,
        sample_size=sample_size,
        count=count,
    )

    data_from_db = data_storage.get_count_data(query)
    if data_from_db is None or len(data_from_db) < count:
        raise ValueError("Not enough data in storage.")

    for sample_data in data_from_db:
        sample = sample_data.data
        data.append(sample)

    return data
