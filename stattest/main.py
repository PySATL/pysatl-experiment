import logging
import sys
from typing import Any

from stattest import __version__
from stattest.commands.arguments import Arguments
from stattest.constants import DOCS_LINK
from stattest.exceptions import ConfigurationError, OperationalException
from stattest.system.gc_setup import gc_set_threshold
from stattest.system.version_info import print_version_info


logger = logging.getLogger(__name__)


def main(sysargv: list[str] | None = None) -> None:
    return_code: Any = 1
    try:
        arguments = Arguments(sysargv)
        args = arguments.get_parsed_arg()

        # Call subcommand.
        if args.get("version") or args.get("version_main"):
            print_version_info()
            return_code = 0
        elif "func" in args:
            logger.info(f"PySATL Experiment {__version__}")
            gc_set_threshold()
            return_code = args["func"](args)
        else:
            # No subcommand was issued.
            raise OperationalException(
                "Usage of PySATL requires a subcommand to be specified.\n"
                "To see the full list of options available, please use "
                "`pysatl --help` or `pysatl <command> --help`."
            )
    except SystemExit as e:  # pragma: no cover
        return_code = e
    except KeyboardInterrupt:
        logger.info("SIGINT received, aborting ...")
        return_code = 0
    except ConfigurationError as e:
        logger.error(
            f"Configuration error: {e}\n"
            f"Please make sure to review the documentation at {DOCS_LINK}."
        )
    except Exception:
        logger.exception("Fatal exception!")
    finally:
        sys.exit(return_code)


if __name__ == "__main__":
    main()
