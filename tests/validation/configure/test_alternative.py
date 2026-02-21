from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.alternatives.alternatives import alternatives
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.experiment.generator import AbstractRVSGenerator


class NormalGenerator(AbstractRVSGenerator):
    def __init__(self, loc: float, scale: float, **kwargs):
        super().__init__(**kwargs)
        self.loc = loc
        self.scale = scale


class CauchyGenerator(AbstractRVSGenerator):
    def __init__(self, x0: float, gamma: float, **kwargs):
        super().__init__(**kwargs)
        self.x0 = x0
        self.gamma = gamma


class NormalDistribution(AbstractRVSGenerator):
    def __init__(self, mean: float, std: float, **kwargs):
        super().__init__(**kwargs)
        self.mean = mean
        self.std = std


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.get_experiment_name_and_config")
def test_alternatives_fails_if_experiment_type_not_set(
    mock_get_config: MagicMock, mock_save_config: MagicMock, runner: CliRunner
) -> None:
    experiment_name = "my-exp"
    mock_get_config.return_value = (experiment_name, {})

    result = runner.invoke(alternatives, ["--alt", "Normal 1 1"])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)
    assert "Experiment type is not configured" in result.output
    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.validation.cli.schemas.alternative.AbstractRVSGenerator.__subclasses__",
    return_value=[NormalGenerator],
)
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.get_experiment_name_and_config")
def test_alternatives_fails_for_unsupported_experiment_type(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_subclasses: MagicMock, runner: CliRunner
) -> None:
    """
    Tests that the command fails if alternatives are provided for a non-POWER experiment.
    """
    mock_get_config.return_value = ("my-exp", {"experiment_type": ExperimentType.CRITICAL_VALUE.value})

    result = runner.invoke(alternatives, ["--alt", "Normal 1 1"])

    assert result.exit_code != 0
    assert "Alternatives are not supported for the experiment type 'critical_value'" in result.output
    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.validation.cli.schemas.alternative.AbstractRVSGenerator.__subclasses__",
    return_value=[NormalGenerator],
)
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.get_experiment_name_and_config")
def test_alternatives_fails_with_wrong_parameter_count(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_subclasses: MagicMock, runner: CliRunner
) -> None:
    mock_get_config.return_value = ("my-exp", {"experiment_type": "power"})
    result = runner.invoke(alternatives, ["--alt", "Normal 1.0"])

    assert result.exit_code != 0
    expected_error = (
        "For alternative #1 ('Normal 1.0'): Value error, "
        "Generator 'NORMALGENERATOR' expects 2 unique parameters (loc, scale), but received 1."
    )
    assert expected_error in result.output
    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.validation.cli.schemas.alternative.AbstractRVSGenerator.__subclasses__",
    return_value=[NormalGenerator],
)
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.get_experiment_name_and_config")
def test_alternatives_fails_with_non_numeric_parameters(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_subclasses: MagicMock, runner: CliRunner
) -> None:
    mock_get_config.return_value = ("my-exp", {"experiment_type": "power"})
    result = runner.invoke(alternatives, ["--alt", "Normal 1.0 abc"])

    assert result.exit_code != 0
    expected_error = (
        "For alternative #1 ('Normal 1.0 abc'): Value error, All parameters for generator 'Normal' must be numbers."
    )
    assert expected_error in result.output
    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.validation.cli.schemas.alternative.AbstractRVSGenerator.__subclasses__",
    return_value=[NormalGenerator, NormalDistribution],  # type: ignore
)
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.get_experiment_name_and_config")
def test_alternatives_fails_with_ambiguous_generator_name(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_subclasses: MagicMock, runner: CliRunner
) -> None:
    """
    Tests failure when a generator prefix matches multiple available generators.
    """
    mock_get_config.return_value = ("my-exp", {"experiment_type": "power"})
    result = runner.invoke(alternatives, ["--alt", "Normal 1 2"])

    assert result.exit_code != 0

    output = result.output

    assert "For alternative #1 ('Normal 1 2')" in output
    assert "Generator prefix 'Normal' is ambiguous" in output
    assert "NORMALGENERATOR" in output
    assert "NORMALDISTRIBUTION" in output
    assert "Please be more specific" in output

    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.validation.cli.schemas.alternative.AbstractRVSGenerator.__subclasses__",
    return_value=[NormalGenerator, CauchyGenerator],  # type: ignore
)
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.alternatives.alternatives.get_experiment_name_and_config")
def test_alternatives_success_with_valid_inputs(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_subclasses: MagicMock, runner: CliRunner
) -> None:
    experiment_name = "my-power-exp"
    initial_config = {"experiment_type": "power"}
    mock_get_config.return_value = (experiment_name, initial_config.copy())

    result = runner.invoke(alternatives, ["--alt", "NormalG 1.0 0.5", "--alt", "cauchy 0 2"])

    assert result.exit_code == 0
    assert result.exception is None

    mock_save_config.assert_called_once()

    saved_config = mock_save_config.call_args[0][2]

    assert "alternatives" in saved_config
    assert len(saved_config["alternatives"]) == 2
    assert saved_config["alternatives"][0]["generator_name"] == "NORMALGENERATOR"
    assert saved_config["alternatives"][0]["parameters"] == [1.0, 0.5]
    assert saved_config["alternatives"][1]["generator_name"] == "CAUCHYGENERATOR"
    assert saved_config["alternatives"][1]["parameters"] == [0.0, 2.0]

    assert f"Alternatives of the experiment '{experiment_name}' are successfully set." in result.output
    assert "Configured alternatives:" in result.output
    assert "  - NORMALGENERATOR 1.0 0.5" in result.output
    assert "  - CAUCHYGENERATOR 0.0 2.0" in result.output
