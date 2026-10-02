"""Shared contracts can be imported without loading concrete execution or storage code."""

import subprocess
import sys


def test_contract_imports_do_not_load_implementations():
    code = """
import sys
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
assert not any(name.startswith("pysatl_experiment.experiment_execution.step.") for name in sys.modules)
assert not any(name.startswith("pysatl_experiment.persistence.sqlalchemy") for name in sys.modules)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_scheduler_import_does_not_load_experiments_or_storage():
    code = """
import sys
from pysatl_experiment.parallel import Scheduler, no_context
assert not any(name.startswith("pysatl_experiment.experiment_execution") for name in sys.modules)
assert not any(name.startswith("pysatl_experiment.persistence") for name in sys.modules)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
