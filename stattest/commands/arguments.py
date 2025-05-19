from argparse import ArgumentParser, Namespace, _ArgumentGroup
from typing import Any

from stattest.commands.cli_options import AVAILABLE_CLI_OPTIONS


ARGS_COMMON = ["logfile", "config", "version"]

ARGS_EXPERIMENT = []


class Arguments:
    """
    Arguments Class. Manage the arguments received by the cli
    """

    def __init__(self, args: list[str] | None) -> None:
        self.parser = None
        self.args = args
        self._parsed_arg: Namespace | None = None

    def get_parsed_arg(self) -> dict[str, Any]:
        """
        Return the list of arguments
        :return: List[str] List of arguments
        """
        if self._parsed_arg is None:
            self._build_subcommands()
            self._parsed_arg = self._parse_args()

        return vars(self._parsed_arg)

    def _parse_args(self) -> Namespace:
        """
        Parses given arguments and returns an argparse Namespace instance.
        """
        parsed_arg = self.parser.parse_args(self.args)

        return parsed_arg

    def _build_args(self, optionlist: list[str], parser: ArgumentParser | _ArgumentGroup) -> None:
        for val in optionlist:
            opt = AVAILABLE_CLI_OPTIONS[val]
            parser.add_argument(*opt.cli, dest=val, **opt.kwargs)

    def _build_subcommands(self) -> None:
        """
        Builds and attaches all subcommands.
        :return: None
        """
        # Build shared arguments (as group Common Options)
        _common_parser = ArgumentParser(add_help=False)
        group = _common_parser.add_argument_group("Common arguments")
        self._build_args(optionlist=ARGS_COMMON, parser=group)

        # Build main command
        self.parser = ArgumentParser(prog="statest", description="Free, open source statistic lib")

        from stattest.commands import start_experiment

        subparsers = self.parser.add_subparsers(
            dest="command",
            # Use custom message when no subhandler is added
            # shown from `main.py`
            # required=True
        )

        # Add trade subcommand
        trade_cmd = subparsers.add_parser(
            "experiment", help="Experiment module.", parents=[_common_parser]
        )
        trade_cmd.set_defaults(func=start_experiment)
        self._build_args(optionlist=ARGS_EXPERIMENT, parser=trade_cmd)
