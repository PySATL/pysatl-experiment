# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom RVS generators
"""

import logging
from typing import Any, Optional

from stattest.constants import USERPATH_BUILDERS
from stattest.exceptions import OperationalException
from stattest.experiment.configuration import ReportBuilder
from stattest.resolvers.iresolver import IResolver

logger = logging.getLogger(__name__)


class BuilderResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = ReportBuilder
    object_type_str = "ReportBuilder"
    user_subdir = USERPATH_BUILDERS
    initial_search_path = None
    extra_path = "builder_path"
    module_names = ["stattest.experiment.report"]

    @staticmethod
    def load(
            builder_name: str, path: Optional[str] = None, params: Optional[dict[str, Any]] = None
    ) -> ReportBuilder:

        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param builder_name:
        """

        builder: ReportBuilder = BuilderResolver._load(
            builder_name, params=params, extra_dir=path
        )

        return builder

    @staticmethod
    def validate_generator(builder: ReportBuilder) -> ReportBuilder:
        # Validation can be added
        return builder

    @staticmethod
    def _load(
            builder_name: str,
            params: Optional[dict[str, Any]],
            extra_dir: Optional[str] = None,
    ) -> ReportBuilder:
        """
        Search and loads the specified strategy.
        :param builder_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = BuilderResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_BUILDERS, extra_dirs=extra_dirs
        )
        # TODO: 'E:/Documents/Projects/PySATL/pysatl-experiment/tests/resolvers/generator_path')

        worker = BuilderResolver._load_object(
            paths=abs_paths,
            object_name=builder_name,
            add_source=True,
            kwargs=params,
        )

        if not worker:
            worker = BuilderResolver._load_modules_object(
                object_name=builder_name, kwargs=params
            )

        if worker:
            return BuilderResolver.validate_generator(worker)

        raise OperationalException(
            f"Impossible to load RVS generator '{builder_name}'. This class does not exist "
            "or contains Python code errors."
        )
