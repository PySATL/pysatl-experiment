from stattest.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


class SQLiteTimeComplexityStorage(ITimeComplexityStorage):
    """
    SQLite time complexity storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def init(self) -> None:
        """
        Initialize SQLite time complexity storage.

        :return: None
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

    def delete_data(self, query: TimeComplexityQuery) -> None:
        """
        Delete time complexity data from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")
