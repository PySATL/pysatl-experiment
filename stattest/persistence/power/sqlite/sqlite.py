from stattest.persistence.model.power.power import PowerQuery, PowerModel


class SQLitePowerStorage:
    """
    SQLite power storage.
    """
    def __init__(self, connection: str):
        self.connection = connection

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
