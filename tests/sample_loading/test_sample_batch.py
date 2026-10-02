"""Sample batches preserve identity and reject incomplete or mixed datasets."""

from unittest.mock import Mock, patch

import pytest

from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_worker import (
    TimeComplexityWorker,
)
from pysatl_experiment.persistence.models.random_values import RandomValuesModel
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage
from pysatl_experiment.sample_loading.loading import load_sample_batch
from pysatl_experiment.types import Sample, SampleBatch, SampleSetSpec


def make_spec(**changes):
    return SampleSetSpec(
        **(
            dict(
                experiment_name="experiment",
                generator_code="normal_mean_1.0",
                sample_size=2,
                samples_count=2,
            )
            | changes
        )
    )


@pytest.mark.parametrize("samples", [[], [Sample([1.0, 2.0])], [Sample([1.0]), Sample([2.0, 3.0])]])
def test_batch_rejects_wrong_count_or_size(samples):
    with pytest.raises(ValueError):
        SampleBatch(make_spec(), samples)


def test_loading_filters_series_before_limiting_count(tmp_path):
    storage = AlchemyRandomValuesStorage(f"sqlite:///{tmp_path / 'samples.db'}")
    storage.init()
    storage.bulk_insert(
        [
            RandomValuesModel("experiment", f"normal_mean_{mean}", {"mean": mean}, 2, [mean, mean])
            for mean in [0.0, 1.0, 0.0, 1.0, 0.0]
        ]
    )
    batch = load_sample_batch(storage, make_spec())
    assert batch.spec == make_spec()
    assert [sample.values for sample in batch.samples] == [[1.0, 1.0], [1.0, 1.0]]
    with pytest.raises(ValueError, match="Not enough data"):
        load_sample_batch(storage, make_spec(samples_count=3))


def test_worker_passes_original_values_and_records_each_duration():
    values = [1.0, 2.0]
    batch = SampleBatch(make_spec(), [Sample(values), Sample([3.0, 4.0])])
    statistic = Mock()
    with patch(
        "pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_worker.perf_counter",
        side_effect=[1.0, 1.25, 2.0, 2.5],
    ):
        result = TimeComplexityWorker(statistic, batch).execute()
    assert result.results_times == [0.25, 0.5]
    assert statistic.execute_statistic.call_args_list[0].kwargs["rvs"] is values


def test_loading_range_uses_series_identity_instead_of_realized_parameters(tmp_path):
    storage = AlchemyRandomValuesStorage(f"sqlite:///{tmp_path / 'ranges.db'}")
    storage.init()
    code = "normal_mean_[0.0,1.0]"
    rows = [
        RandomValuesModel("experiment", code, {"mean": mean}, 2, [mean, mean]) for mean in (0.1, 0.8)
    ]
    storage.bulk_insert([
        RandomValuesModel("experiment", "normal_mean_[0.0,2.0]", {"mean": 0.1}, 2, [-1.0, -1.0]),
        RandomValuesModel("experiment", "normal_mean_0.1", {"mean": 0.1}, 2, [-2.0, -2.0]),
        *rows,
    ])
    batch = load_sample_batch(storage, make_spec(generator_code=code))
    assert [sample.values for sample in batch.samples] == [row.data for row in rows]
    with pytest.raises(ValueError, match="Not enough data"):
        load_sample_batch(storage, make_spec(generator_code=code, samples_count=3))
