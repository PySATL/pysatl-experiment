from stattest.persistence.model.random_values.random_values import IRandomValuesStorage, RandomValuesCountQuery


def get_sample_data_from_storage(
    generator_name: str,
    generator_parameters: list[float],
    sample_size: int,
    count: int,
    data_storage: IRandomValuesStorage,
) -> list[list[float]]:
    """
    Get data from storage based on the hypothesis and sample size.

    :param generator_name: generator name.
    :param generator_parameters: generator parameters.
    :param sample_size: sample_size.
    :param count: count of samples to get.
    :param data_storage: data storage.

    :return: data.
    """

    data = []

    query = RandomValuesCountQuery(
        generator_name=generator_name, generator_parameters=generator_parameters, sample_size=sample_size, count=count
    )

    data_from_db = data_storage.get_count_data(query)
    if data_from_db is None or len(data_from_db) < count:
        raise ValueError("Not enough data in storage.")

    for sample_data in data_from_db:
        sample = sample_data.data
        data.append(sample)

    return data
