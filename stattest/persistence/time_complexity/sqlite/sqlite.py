from stattest.persistence.model.time_complexity.time_complexity import (
    TimeComplexityModel,
    TimeComplexityQuery, ITimeComplexityStorage,
)


class SQLiteTimeComplexityStorage(ITimeComplexityStorage):
    """
    SQLite time complexity storage.
    """

    def __init__(self, connection: str):
        self.connection = connection

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
