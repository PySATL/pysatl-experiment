"""Typed iterator over stored random samples."""

from pysatl_experiment.persistence.bulk_iterator import BulkDataIterator
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter, RandomValuesModel


class RandomValuesIterator(BulkDataIterator[RandomValuesModel, RandomValuesFilter]):
    """Lazily traverse random samples in bounded pages."""
