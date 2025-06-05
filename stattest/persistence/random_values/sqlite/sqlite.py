from stattest.persistence.model.random_values.random_values import (
    RandomValuesModel,
    RandomValuesQuery, IRandomValuesStorage,
)


class SQLiteRandomValuesStorage(IRandomValuesStorage):
    """
    SQLite random values storage.
    """

    def __init__(self, connection: str):
        self.connection = connection

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

    def get_rvs_count(self, query: RandomValuesQuery) -> int:
        """
        Get count of samples in SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")
