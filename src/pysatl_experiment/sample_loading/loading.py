"""Load a validated sample batch through the storage contract."""

from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter
from pysatl_experiment.persistence.random_values_iterator import RandomValuesIterator
from pysatl_experiment.types import Sample, SampleBatch, SampleSetSpec


def load_sample_batch(storage: IRandomValuesStorage, spec: SampleSetSpec) -> SampleBatch:
    """Load a series whose code identifies fixed parameters and configured ranges."""
    query = RandomValuesFilter(
        experiment_name=spec.experiment_name,
        generator_code=spec.generator_code,
        sample_size=spec.sample_size,
    )
    samples = []
    for row in RandomValuesIterator(storage, query, batch_size=min(1000, spec.samples_count)):
        samples.append(Sample(values=row.data))
        if len(samples) == spec.samples_count:
            break
    if len(samples) < spec.samples_count:
        raise ValueError("Not enough data in storage for the requested sample set.")
    return SampleBatch(spec=spec, samples=samples)
