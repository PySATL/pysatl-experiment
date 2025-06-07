from stattest.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)


class SQLiteRandomValuesStorage(IRandomValuesStorage):
    """
    SQLite random values storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def init(self) -> None:
        """
        Initialize SQLite random values storage.

        :return: None
        """

    def get_data(self, query: RandomValuesQuery) -> RandomValuesModel:
        """
        Get random values data from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def insert_data(self, data: RandomValuesModel) -> None:
        """
        Insert random values data to SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """
        Get count of samples in SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def delete_data(self, query: RandomValuesQuery) -> None:
        """
        Delete random values data from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def insert_all_data(self, query: RandomValuesAllModel) -> None:
        """
        Insert all data into SQLite storage based on hypothesis and sample size.
        """
        raise NotImplementedError("Method is not yet implemented")

    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel]:
        """
        Get all data from SQLite storage based on hypothesis and sample size.
        """
        raise NotImplementedError("Method is not yet implemented")

    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """
        Delete all data from SQLite storage based on hypothesis and sample size.
        """
        raise NotImplementedError("Method is not yet implemented")

    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel]:
        """
        Get count data based on hypothesis and sample size.
        """
        raise NotImplementedError("Method is not yet implemented")
