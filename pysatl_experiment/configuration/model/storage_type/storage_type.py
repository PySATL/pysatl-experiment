from enum import Enum


class StorageType(Enum):
    """
    Internal storage.
    """

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
