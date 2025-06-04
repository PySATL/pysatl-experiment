from stattest.persistence.model.time_complexity.time_complexity import TimeComplexityQuery, TimeComplexityModel


class SQLiteTimeComplexityStorage:
    """
    SQLite time complexity storage.
    """

    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel:
        """
        Get time complexity data from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def insert_data(self, data: TimeComplexityModel) -> None:
        """
        Insert time complexity data to SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")
