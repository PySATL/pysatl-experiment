"""
Database validation helpers.

This module provides utility classes used during configuration validation.
The main purpose is verifying that required precomputed critical values
exist in the configured SQLite database before a power experiment starts.
"""

from sqlalchemy import create_engine, text


class SQLiteCriticalValueChecker:
    """
    Validator for checking the existence of critical values in SQLite storage.

    The checker establishes a database connection and provides methods
    for verifying whether critical values for specific criteria and
    sample sizes are already available.
    """

    def __init__(self, connection_string: str):
        """
        Initialize database checker.

        Parameters
        ----------
        connection_string : str
            SQLAlchemy connection URL.

        Raises
        ------
        ConnectionError
            If the database connection cannot be established.
        """
        self.connection_string = connection_string
        self.engine = None
        try:
            self.engine = create_engine(connection_string)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            raise ConnectionError(f"Failed to connect to the database '{self.connection_string}': {e}")

    def check_exists(self, criterion_code: str, sample_size: int) -> bool:
        """
        Check whether critical values exist.

        Parameters
        ----------
        criterion_code : str
            Criterion identifier.
        sample_size : int
            Sample size.

        Returns
        -------
        bool
            True if matching critical values exist, otherwise False.

        Notes
        -----
        The lookup is performed against the ``limit_distributions`` table.
        """
        if self.engine is None:
            return False

        sql = text("""
            SELECT EXISTS (
                SELECT 1
                FROM limit_distributions
                WHERE criterion_code = :criterion_code
                  AND sample_size = :sample_size
            )
        """)

        with self.engine.connect() as conn:
            result = conn.execute(
                sql,
                {
                    "criterion_code": criterion_code,
                    "sample_size": sample_size,
                },
            )
            return result.scalar() == 1
