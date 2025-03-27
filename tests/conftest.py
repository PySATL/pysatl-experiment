import pytest


@pytest.fixture()
def keep_log_config_loggers(mocker):
    # Mock the _handle_existing_loggers function to prevent it from disabling all loggers.
    # This is necessary to keep all loggers active, and avoid random failures if
    # this file is ran before the test_rest_client file.
    mocker.patch("logging.config._handle_existing_loggers")


@pytest.fixture(scope="function")
def import_fails() -> None:
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
