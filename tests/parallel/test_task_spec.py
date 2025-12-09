import pickle
import pytest
from pysatl_experiment.parallel.task_spec import TaskSpec


class TestTaskSpec:

    def test_basic_creation(self):
        spec = TaskSpec(
            experiment_type="time_complexity",
            statistic_class_name="KS",
            statistic_module="module.ks",
            sample_size=100,
            monte_carlo_count=1000,
            db_path="/tmp/test.db",
        )
        assert spec.experiment_type == "time_complexity"
        assert spec.sample_size == 100

    @pytest.mark.parametrize("exp_type", ["time_complexity", "critical_value", "power"])
    def test_all_experiment_types(self, exp_type, temp_db_path):
        spec = TaskSpec(
            experiment_type=exp_type,
            statistic_class_name="TestStat",
            statistic_module="test.module",
            sample_size=50,
            monte_carlo_count=100,
            db_path=temp_db_path,
        )
        assert spec.experiment_type == exp_type

    def test_power_specific_fields(self, temp_db_path):
        spec = TaskSpec(
            experiment_type="power",
            statistic_class_name="SW",
            statistic_module="sw",
            sample_size=200,
            monte_carlo_count=500,
            db_path=temp_db_path,
            alternative_generator="EXP",
            alternative_parameters=[1.0, 2.0],
            significance_level=0.01,
        )
        assert spec.alternative_generator == "EXP"
        assert spec.significance_level == 0.01

    def test_pickle_serialization_roundtrip(self, temp_db_path):
        original = TaskSpec(
            experiment_type="critical_value",
            statistic_class_name="AD",
            statistic_module="ad",
            sample_size=150,
            monte_carlo_count=200,
            db_path=temp_db_path,
            hypothesis_generator="NORM",
            hypothesis_parameters=[0.0, 1.0],
        )

        pickled = pickle.dumps(original)
        restored = pickle.loads(pickled)

        assert restored.__dict__ == original.__dict__

    def test_mutable_defaults_safety(self):
        spec1 = TaskSpec(
            experiment_type="time_complexity",
            statistic_class_name="X",
            statistic_module="x",
            sample_size=10,
            monte_carlo_count=10,
            db_path="/tmp/1.db",
        )
        spec2 = TaskSpec(
            experiment_type="time_complexity",
            statistic_class_name="Y",
            statistic_module="y",
            sample_size=10,
            monte_carlo_count=10,
            db_path="/tmp/2.db",
        )

        spec1.hypothesis_parameters.append(999)

        assert spec2.hypothesis_parameters == []
