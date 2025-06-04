from stattest.persistence.model.random_values.random_values import RandomValuesQuery, RandomValuesModel
from stattest.persistence.model.time_complexity.time_complexity import TimeComplexityQuery, TimeComplexityModel


class SQLiteRandomValuesStorage:
    """
    SQLite random values storage.
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

    def get_rvs_count(self, query: RandomValuesQuery) -> int:
        """
        Get count of samples in SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")
