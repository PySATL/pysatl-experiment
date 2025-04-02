# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom statistic tests
"""

import logging
from typing import Any

from pysatl.criterion import AbstractStatistic

from stattest.constants import USERPATH_TESTS
from stattest.exceptions import OperationalException
from stattest.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class TestResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = AbstractStatistic
    object_type_str = "AbstractTestStatistic"
    user_subdir = USERPATH_TESTS
    initial_search_path = None
    extra_path = "test_path"
    module_names = ["pysatl.criterion"]

    @staticmethod
    def load(
        name: str, path: str | None = None, params: dict[str, Any] | None = None
    ) -> AbstractStatistic:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param name:
        """

        test: AbstractStatistic = TestResolver._load(name, params=params, extra_dir=path)

        return test

    @staticmethod
    def validate(test: AbstractStatistic) -> AbstractStatistic:
        # Validation can be added
        return test

    @staticmethod
    def _load(
        test_name: str,
        params: dict[str, Any] | None,
        extra_dir: str | None = None,
    ) -> AbstractStatistic:
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

        test = TestResolver._load_object(
            paths=abs_paths,
            object_name=test_name,
            add_source=True,
            kwargs=params,
        )

        if not test:
            test = TestResolver._load_modules_object(object_name=test_name, kwargs=params)

        if test:
            return TestResolver.validate(test)

        raise OperationalException(
            f"Impossible to load RVS generator '{test_name}'. This class does not exist "
            "or contains Python code errors."
        )
