"""Tests for garbage collector tuning in the CLI group callback."""

from unittest.mock import patch

import click
from click.testing import CliRunner

from pysatl_experiment.cli.shared import cli


def probe_callback() -> None:
    """No-op callback used to observe the group callback side effects."""


# Checks that the group callback tunes the garbage collector before a subcommand runs.
def test_group_callback_tunes_garbage_collector() -> None:
    cli.add_command(click.Command("probe-gc", callback=probe_callback))
    try:
        with (
            patch("pysatl_experiment.cli.shared.ensure_experiment_dir"),
            patch("pysatl_experiment.cli.shared.gc_set_threshold") as gc_set_threshold,
        ):
            result = CliRunner().invoke(cli, ["probe-gc"])
    finally:
        cli.commands.pop("probe-gc", None)

    assert result.exit_code == 0
    gc_set_threshold.assert_called_once_with()


# Checks that eager options exit before the group callback, so GC tuning is skipped.
def test_eager_options_do_not_tune_garbage_collector() -> None:
    with patch("pysatl_experiment.cli.shared.gc_set_threshold") as gc_set_threshold:
        version_result = CliRunner().invoke(cli, ["--version"])
        help_result = CliRunner().invoke(cli, ["--help"])

    assert version_result.exit_code == 0
    assert help_result.exit_code == 0
    gc_set_threshold.assert_not_called()
