from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType


class NormalGenerator:
    def __init__(self, loc: float, scale: float, **kwargs):
        super().__init__(**kwargs)
        self.loc = loc
        self.scale = scale


class CauchyGenerator:
    def __init__(self, x0: float, gamma: float, **kwargs):
        super().__init__(**kwargs)
        self.x0 = x0
        self.gamma = gamma

@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.configure.get_experiment_config")
def test_alternatives_fails_if_experiment_type_not_set(
    get_experiment_config: MagicMock, runner: CliRunner
) -> None:
    experiment_name = "my-exp"
    get_experiment_config.return_value = (experiment_name, {"some_key": "some_value"})

    result = runner.invoke(configure, [experiment_name, "-alt", "Normal 1 1",
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite",
                                         "-rm", "reuse"])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)


@patch("pysatl_experiment.cli.commands.configure.configure.get_experiment_config")
def test_alternatives_fails_for_unsupported_experiment_type(
    get_experiment_config: MagicMock, runner: CliRunner
) -> None:
    """
    Tests that the command fails if alternatives are provided for a non-POWER experiment.
    """
    experiment_name = "my-exp"
    get_experiment_config.return_value = ("my-exp", {"experiment_type": ExperimentType.CRITICAL_VALUE.value})

    result = runner.invoke(configure, [experiment_name, "-alt", "Normal 1 1",
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite",
                                         "-rm", "reuse"])

    assert result.exit_code != 0


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_alternatives_fails_with_wrong_parameter_count(
        if_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner
) -> None:
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {'name': experiment_name, 'config': initial_config}
    result = runner.invoke(configure, [experiment_name, "-alt", "Normal 1.0",
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite",
                                         "-rm", "reuse"])

    assert result.exit_code != 0


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_alternatives_fails_with_non_numeric_parameters(
        if_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner
) -> None:
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {'name': experiment_name, 'config': initial_config}
    result = runner.invoke(configure, [experiment_name, "-alt", "Normal 1.0 abc",
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite",
                                         "-rm", "reuse"])

    assert result.exit_code != 0


@patch(
    "pysatl_experiment.validation.cli.schemas.alternative.AbstractRVSGenerator.__subclasses__",
    return_value=[NormalGenerator, CauchyGenerator, NormalGenerator],  # type: ignore
)
@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_alternatives_fails_with_ambiguous_generator_name(
        if_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        subclasses: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner
) -> None:
    """
    Tests failure when a generator prefix matches multiple available generators.
    """
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {'name': experiment_name, 'config': initial_config}
    result = runner.invoke(configure, [experiment_name, "-alt", "Normal 1 2",
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "power", "-con", "sqlite:///pysatl.sqlite",
                                         "-rm", "reuse"])

    assert result.exit_code != 0

    output = result.output

    assert "For alternative #1 ('Normal 1 2')" in output
    assert "Generator prefix 'Normal' is ambiguous" in output
    assert "NORMALGENERATOR" in output
    assert "Please be more specific" in output


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_alternatives_success_with_valid_inputs(
        if_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner
) -> None:
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {'name': experiment_name, 'config': initial_config}
    result = runner.invoke(configure, [experiment_name, "-alt", "NormalG 1.0 0.5", "-alt", "cauchy 0 2",
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "power", "-con", "sqlite:///pysatl.sqlite",
                                       "-rm", "reuse"])

    assert result.exit_code == 0
    assert result.exception is None

    assert "alternatives" in initial_config
    assert len(initial_config["alternatives"]) == 2
    assert initial_config["alternatives"][0]["generator_name"] == "NORMALGENERATOR"
    assert initial_config["alternatives"][0]["parameters"] == [1.0, 0.5]
    assert initial_config["alternatives"][1]["generator_name"] == "CAUCHYRVSGENERATOR"
    assert initial_config["alternatives"][1]["parameters"] == [0.0, 2.0]
