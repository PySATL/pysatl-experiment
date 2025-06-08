from stattest.persistence.model.experiment.experiment import (
    ExperimentModel,
    ExperimentQuery,
    IExperimentStorage,
)


class SQLiteExperimentStorage(IExperimentStorage):
    """
    SQLite experiment config storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def init(self) -> None:
        """
        Initialize SQLite experiment config storage.

        :return: None
        """

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

    def delete_data(self, query: ExperimentQuery) -> None:
        """
        Delete experiment config from SQLite storage.
        """
        raise NotImplementedError("Method is not yet implemented")

    def get_experiment_id(self, query: ExperimentQuery) -> int:
        """
        Get experiment id from SQLite storage.

        :return: experiment id
        """
        raise NotImplementedError("Method is not yet implemented")
