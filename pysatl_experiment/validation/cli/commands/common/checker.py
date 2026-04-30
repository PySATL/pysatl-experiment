from sqlalchemy import create_engine, text


class SQLiteCriticalValueChecker:
    """
    Checks for the existence of pre-calculated critical values
    in an SQLite database, using the same query pattern as
    StorageCriticalValueResolver.
    """

    def __init__(self, connection_string: str):
        """
        Args:
            connection_string: SQLAlchemy URL for the SQLite database.

        Raises:
            ConnectionError: If the connection fails.
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
        Checks if critical values exist for the given criterion and sample size.

        Mirrors the query used by StorageCriticalValueResolver:
        selects by criterion_code + sample_size from limit_distributions.

        Args:
            criterion_code: Full criterion name (e.g., "KS_NORMALITY_GOODNESS_OF_FIT").
            sample_size: Sample size used for the calculation.

        Returns:
            True if a matching record exists, False otherwise.
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
