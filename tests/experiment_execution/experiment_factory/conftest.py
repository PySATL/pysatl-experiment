"""Validated configurations and isolated stores for assembly and planning tests."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pysatl_experiment.configuration.config_loader import read_raw_experiment_config
from pysatl_experiment.configuration import RawExperimentConfig
from pysatl_experiment.configuration.validation import validate_experiment_config
from pysatl_experiment.experiment_execution.experiment_storages import ExperimentStorages
from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry


@pytest.fixture
def make_config(tmp_path):
    examples = Path(__file__).resolve().parents[3] / "experiment_example/configs"
    paths = {
        "critical_value": "critical_values/normal_critical_values.json",
        "power": "power/normal_power.json",
        "time_complexity": "time_complexity/laplace_time_complexity.json",
    }

    def build(kind, run_mode="reuse"):
        document = read_raw_experiment_config(examples / paths[kind]).to_dict()
        document["storage_connection"] = f"sqlite:///{tmp_path / 'experiment.sqlite'}"
        document["run_mode"] = run_mode
        document["report"]["results_path"] = str(tmp_path / "reports")
        document["execute"]["monte_carlo_count"] = 100
        document["execute"]["criteria"] = document["execute"]["criteria"][:1]
        # Keep assembly fixtures fixed-size when users extend the example configurations.
        document["generate"]["distributions"] = document["generate"]["distributions"][:1]
        document["execute"]["significance_levels"] = [0.05, 0.1]
        if kind == "power":
            document["execute"]["sample_sizes"] = [10, 20]
        else:
            document["generate"]["sample_sizes"] = [10, 20]
            document["generate"]["samples_count"] = 100
        return validate_experiment_config(RawExperimentConfig(document))

    return build


@pytest.fixture(params=["critical_value", "power", "time_complexity"])
def config(request, make_config):
    return make_config(request.param)


@pytest.fixture
def definition(config):
    return create_default_experiment_registry(load_plugins=False).get(config.experiment_type)


@pytest.fixture
def storages():
    result = ExperimentStorages(data=Mock(), result=Mock(), experiment=Mock())
    result.data.count.return_value = 0
    result.result.get_data.return_value = None
    result.experiment.get_data.return_value = None
    return result
