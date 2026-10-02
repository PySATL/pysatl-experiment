"""Repeatable exact selection of timing results using paginated reads."""

from collections.abc import Iterable, Iterator

from pysatl_experiment.persistence.contracts.time_complexity import ITimeComplexityStorage
from pysatl_experiment.persistence.models.time_complexity import (
    TimeComplexityFilter,
    TimeComplexityModel,
    TimeComplexityQuery,
)
from pysatl_experiment.persistence.time_complexity_iterator import TimeComplexityIterator
from pysatl_experiment.persistence.validation import require_nonempty_name, require_positive_integer


class TimeComplexityResults:
    """Check completeness and reject duplicate timing records before reporting."""

    def __init__(
        self,
        storage: ITimeComplexityStorage,
        experiment_name: str,
        queries: Iterable[TimeComplexityQuery],
        *,
        read_batch_size: int = 1000,
    ) -> None:
        require_nonempty_name(experiment_name, "experiment_name")
        require_positive_integer(read_batch_size, "read_batch_size")
        self.storage = storage
        self.experiment_name = experiment_name
        self.queries = tuple(queries)
        self.read_batch_size = read_batch_size
        if any(query.experiment_name != experiment_name for query in self.queries):
            raise ValueError("All report queries must belong to the selected experiment")

    def __iter__(self) -> Iterator[TimeComplexityModel]:
        """Read and validate a fresh selection on each traversal."""
        return iter(self._load_data())

    @staticmethod
    def _result_key(result: TimeComplexityModel | TimeComplexityQuery):
        return (
            result.experiment_name,
            (
                result.criterion_code,
                tuple(sorted(result.criterion_parameters.items())),
                result.generator_code,
                result.samples_count,
            ),
            result.sample_size,
        )

    def _load_data(self) -> tuple[TimeComplexityModel, ...]:
        """Page through stored results, selecting exact keys and rejecting missing data."""
        expected = {self._result_key(query): query for query in self.queries}
        if not expected:
            return ()
        found = {}
        results = TimeComplexityIterator(
            self.storage,
            TimeComplexityFilter(experiment_name=self.experiment_name),
            batch_size=self.read_batch_size,
        )
        for result in results:
            key = self._result_key(result)
            if key not in expected:
                continue
            if key in found:
                raise ValueError(f"Duplicate time complexity result: {expected[key]}")
            found[key] = result
        missing = [expected[key] for key in sorted(expected.keys() - found.keys())]
        if missing:
            raise ValueError(f"Missing time complexity results: {missing}")
        return tuple(found[key] for key in sorted(expected))
