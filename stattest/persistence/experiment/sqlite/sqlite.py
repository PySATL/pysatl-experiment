from stattest.persistence.model.experiment.experiment import (
    ExperimentModel,
    ExperimentQuery,
    IExperimentStorage,
)


class SQLiteExperimentStorage(IExperimentStorage):
    """
    SQLite experiment config storage.
    """

    def __init__(self, connection: str):
        self.connection = connection

    def get_data(self, query: ExperimentQuery) -> ExperimentModel:
        """
        Get experiment config from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def insert_data(self, data: ExperimentModel) -> None:
        """
        Insert experiment config to SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")
