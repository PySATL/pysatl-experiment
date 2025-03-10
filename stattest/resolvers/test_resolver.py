import logging
from typing import Any, Optional

from stattest.constants import USERPATH_TESTS
from stattest.exceptions import OperationalException
from stattest.resolvers.iresolver import IResolver
from stattest.test import AbstractTestStatistic


logger = logging.getLogger(__name__)


class TestResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = AbstractTestStatistic
    object_type_str = "AbstractTestStatistic"
    user_subdir = USERPATH_TESTS
    initial_search_path = None
    extra_path = "test_path"
    module_names = ["stattest.test"]

    @staticmethod
    def load(
            test_name: str, path: Optional[str] = None, params: Optional[dict[str, Any]] = None
    ) -> AbstractTestStatistic:

        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param test_name:
        """

        test: AbstractTestStatistic = TestResolver._load(
            test_name, params=params, extra_dir=path
        )

        return test

    @staticmethod
    def validate_generator(test: AbstractTestStatistic) -> AbstractTestStatistic:
        # Validation can be added
        return test

    @staticmethod
    def _load(
            test_name: str,
            params: Optional[dict[str, Any]],
            extra_dir: Optional[str] = None,
    ) -> AbstractTestStatistic:
        """
        Search and loads the specified strategy.
        :param test_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = TestResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_TESTS, extra_dirs=extra_dirs
        )
        # TODO: 'E:/Documents/Projects/PySATL/pysatl-experiment/tests/resolvers/generator_path')

        test = TestResolver._load_object(
            paths=abs_paths,
            object_name=test_name,
            add_source=True,
            kwargs=params,
        )

        if not test:
            test = TestResolver._load_modules_object(
                object_name=test_name, kwargs=params
            )

        if test:
            return TestResolver.validate_generator(test)

        raise OperationalException(
            f"Impossible to load RVS generator '{test_name}'. This class does not exist "
            "or contains Python code errors."
        )
