class PySatlException(Exception):
    """
    PySatl base exception. Handled at the outermost level.
    All other exception types are subclasses of this exception type.
    """


class OperationalException(PySatlException):
    """
    Requires manual intervention and will stop execution.
    Most of the time, this is caused by an invalid Configuration.
    """


class ConfigurationError(OperationalException):
    """
    Configuration error. Usually caused by invalid configuration.
    """


class StorageError(OperationalException):  # TODO: description!!!
    """
    Storage error. Used in storage creation.
    """
