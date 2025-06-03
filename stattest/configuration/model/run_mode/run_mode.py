from enum import Enum


class RunMode(Enum):
    """
    Run mode (use existing data in DB or overwrite).
    """
    REUSE = 1
    OVERWRITE = 2
