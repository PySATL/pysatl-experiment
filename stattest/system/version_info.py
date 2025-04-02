from stattest import __version__


def print_version_info():
    """Print version information for pysatl-experiment and its key dependencies."""
    import platform
    import sys

    import ccxt

    print(f"Operating System:\t{platform.platform()}")
    print(f"Python Version:\t\tPython {sys.version.split(' ')[0]}")
    print(f"CCXT Version:\t\t{ccxt.__version__}")
    print()
    print(f"PySATL Experiment Version:\tpysatl-experiment {__version__}")
