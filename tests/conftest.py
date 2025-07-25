from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.criterion.criterion import Criterion
from stattest.configuration.model.report_mode.report_mode import ReportMode


@pytest.fixture()
def keep_log_config_loggers(mocker):
    # Mock the _handle_existing_loggers function to prevent it from disabling all loggers.
    # This is necessary to keep all loggers active, and avoid random failures if
    # this file is ran before the test_rest_client file.
    mocker.patch("logging.config._handle_existing_loggers")


@pytest.fixture(scope="function")
def import_fails() -> Generator[None, None, None]:
    # Source of this test-method:
    # https://stackoverflow.com/questions/2481511/mocking-importerror-in-python
    import builtins

    realimport = builtins.__import__

    def mockedimport(name, *args, **kwargs):
        if name in ["filelock", "cysystemd.journal", "uvloop"]:
            raise ImportError(f"No module named '{name}'")
        return realimport(name, *args, **kwargs)

    builtins.__import__ = mockedimport

    # Run test - then cleanup
    yield

    # restore previous importfunction
    builtins.__import__ = realimport


@pytest.fixture
def mock_criterion():
    mock = MagicMock(spec=Criterion)
    mock.parameters = []
    return mock


@pytest.fixture
def mock_statistics_class():
    return MagicMock(spec=AbstractGoodnessOfFitStatistic)


@pytest.fixture
def mock_criterion_config(mock_criterion, mock_statistics_class):
    return CriterionConfig(
        criterion=mock_criterion,
        criterion_code="KS_",
        statistics_class_object=mock_statistics_class
    )


@pytest.fixture
def results_path(tmp_path):
    path = tmp_path / "reports"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def mock_alternative():
    alt = MagicMock()
    alt.generator_name = "Normal"
    alt.parameters = {"mean": 0, "std": 1}
    return alt


@pytest.fixture
def with_chart():
    return ReportMode.WITH_CHART


@pytest.fixture
def without_chart():
    return ReportMode.WITHOUT_CHART


@pytest.fixture
def cv_values():
    return [1.0] * 8  # 2 criteria × 2 sizes × 2 alphas


@pytest.fixture
def time_data():
    return {
        "KS_": [(10, 0.001), (20, 0.002)],
        "AD_": [(10, 0.0015), (20, 0.0025)]
    }


@pytest.fixture
def power_data():
    return {
        "KS_": {
            ("Normal", 0.05): {10: [True, False, True], 20: [True, True, False]}
        },
        "AD_": {
            ("Normal", 0.05): {10: [False, False, False], 20: [True, False, False]}
        }
    }
