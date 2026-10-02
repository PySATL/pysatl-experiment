"""Typed iterator over stored timing results."""

from pysatl_experiment.persistence.bulk_iterator import BulkDataIterator
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter, TimeComplexityModel


class TimeComplexityIterator(BulkDataIterator[TimeComplexityModel, TimeComplexityFilter]):
    """Lazily traverse timing results in bounded pages."""
