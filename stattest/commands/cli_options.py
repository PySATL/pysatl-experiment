class Arg:
    # Optional CLI arguments
    def __init__(self, *args, **kwargs):
        self.cli = args
        self.kwargs = kwargs


# List of available command line options
AVAILABLE_CLI_OPTIONS = {
    # Common options
    "logfile": Arg(
        "--logfile",
        "--log-file",
        help="Log to the file specified. Special values are: 'syslog', 'journald'. "
        "See the documentation for more details.",
        metavar="FILE",
    ),
    "config": Arg(
        "-c",
        "--config",
        help="Specify configuration file (default: `config/config.json` ",
        action="append",
        metavar="PATH",
    ),
    "version": Arg(
        "-V",
        "--version",
        help="show program's version number and exit",
        action="store_true",
    ),
    "version_main": Arg(
        # Copy of version - used to have -V available with and without subcommand.
        "-V",
        "--version",
        help="show program's version number and exit",
        action="store_true",
    ),
}
