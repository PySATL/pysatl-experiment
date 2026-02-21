import pickle
import tempfile
from pathlib import Path

import pytest

from pysatl_experiment.parallel.task_spec import TaskSpec


class TestTaskSpec:
    def test_basic_creation(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            spec = TaskSpec(
                experiment_type="time_complexity",
                statistic_class_name="KS",
                statistic_module="module.ks",
                sample_size=100,
                monte_carlo_count=1000,
                db_path=db_path,
            )
            assert spec.experiment_type == "time_complexity"
            assert spec.sample_size == 100
        finally:
            Path(db_path).unlink(missing_ok=True)

    @pytest.mark.parametrize("exp_type", ["time_complexity", "critical_value", "power"])
    def test_all_experiment_types(self, exp_type):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            spec = TaskSpec(
                experiment_type=exp_type,
                statistic_class_name="TestStat",
                statistic_module="test.module",
                sample_size=50,
                monte_carlo_count=100,
                db_path=db_path,
            )
            assert spec.experiment_type == exp_type
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_power_specific_fields(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        try:
            spec = TaskSpec(
                experiment_type="power",
                statistic_class_name="SW",
                statistic_module="sw",
                sample_size=200,
                monte_carlo_count=500,
                db_path=db_path,
                alternative_generator="EXP",
                alternative_parameters=[1.0, 2.0],
                significance_level=0.01,
            )
            assert spec.alternative_generator == "EXP"
            assert spec.significance_level == 0.01

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_pickle_serialization_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        try:
            original = TaskSpec(
                experiment_type="critical_value",
                statistic_class_name="AD",
                statistic_module="ad",
                sample_size=150,
                monte_carlo_count=200,
                db_path=db_path,
                hypothesis_generator="NORM",
                hypothesis_parameters=[0.0, 1.0],
            )

            pickled = pickle.dumps(original)
            restored = pickle.loads(pickled)  # noqa: S301

            assert restored.__dict__ == original.__dict__
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_mutable_defaults_safety(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp1:
            db_path1 = tmp1.name
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp2:
            db_path2 = tmp2.name

        try:
            spec1 = TaskSpec(
                experiment_type="time_complexity",
                statistic_class_name="X",
                statistic_module="x",
                sample_size=10,
                monte_carlo_count=10,
                db_path=db_path1,
            )
            spec2 = TaskSpec(
                experiment_type="time_complexity",
                statistic_class_name="Y",
                statistic_module="y",
                sample_size=10,
                monte_carlo_count=10,
                db_path=db_path2,
            )

            spec1.hypothesis_parameters.append(999)

            assert spec2.hypothesis_parameters == []
        finally:
            Path(db_path1).unlink(missing_ok=True)
            Path(db_path2).unlink(missing_ok=True)
