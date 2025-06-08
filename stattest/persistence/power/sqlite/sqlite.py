from stattest.persistence.model.power.power import IPowerStorage, PowerModel, PowerQuery


class SQLitePowerStorage(IPowerStorage):
    """
    SQLite power storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def init(self) -> None:
        """
        Initialize SQLite random values storage.

        :return: None
        """

    def get_data(self, query: PowerQuery) -> PowerModel:
        """
        Get power data from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def insert_data(self, data: PowerModel) -> None:
        """
        Insert power data to SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def delete_data(self, query: PowerQuery) -> None:
        """
        Delete power data from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")
