"""Workers create reusable stores locally and can both write and read data."""

import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import get_ident

import pytest

from pysatl_experiment.parallel import Scheduler
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter, RandomValuesModel
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage


@dataclass
class StorageContext:
    storage: AlchemyRandomValuesStorage
    owner: str
    calls: int = 0


def open_storage(connection: str, log_dir: str) -> StorageContext:
    owner = f"{os.getpid()}-{get_ident()}"
    # Exclusive creation detects accidental reinitialization in the same worker.
    with (Path(log_dir) / owner).open("x") as log:
        log.write("initialized")
    storage = AlchemyRandomValuesStorage(connection)
    storage.init()
    return StorageContext(storage, owner)


@dataclass(frozen=True)
class SaveAndRead:
    value: int

    def __call__(self, context: StorageContext) -> tuple[str, int]:
        assert context.owner == f"{os.getpid()}-{get_ident()}"
        model = RandomValuesModel(f"task-{self.value}", "generator", {}, 1, [float(self.value)])
        context.storage.bulk_insert([model])
        assert context.storage.read_bulk(RandomValuesFilter(experiment_name=model.experiment_name)).items == [model]
        context.calls += 1
        return context.owner, context.calls


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_workers_reuse_local_stores_for_reading_and_writing(tmp_path, backend):
    connection = f"sqlite:///{tmp_path / 'data.db'}"
    log_dir = tmp_path / "initializations"
    log_dir.mkdir()
    storage = AlchemyRandomValuesStorage(connection)
    storage.init()
    with Scheduler(2, partial(open_storage, connection, str(log_dir)), backend=backend) as scheduler:
        results = scheduler.run(SaveAndRead(i) for i in range(8))
    owners = {owner for owner, _ in results}
    assert 1 <= len(owners) <= 2
    assert owners <= {path.name for path in log_dir.iterdir()}
    assert len(list(log_dir.iterdir())) <= 2
    for owner in owners:
        calls = sorted(count for worker, count in results if worker == owner)
        assert calls == list(range(1, len(calls) + 1))
        if backend == "process":
            assert owner.split("-")[0] != str(os.getpid())
    for i in range(8):
        assert storage.count(RandomValuesFilter(experiment_name=f"task-{i}")) == 1
