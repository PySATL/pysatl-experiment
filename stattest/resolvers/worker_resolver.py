# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom RVS generators
"""

import logging
from typing import Any, Optional

from stattest.constants import USERPATH_WORKERS
from stattest.exceptions import OperationalException
from stattest.experiment.test.worker import PowerCalculationWorker
from stattest.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class WorkerResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = PowerCalculationWorker
    object_type_str = "PowerCalculationWorker"
    user_subdir = USERPATH_WORKERS
    initial_search_path = None
    extra_path = "worker_path"
    module_names = ["stattest.experiment.test"]

    @staticmethod
    def load(
        worker_name: str, path: Optional[str] = None, params: Optional[dict[str, Any]] = None
    ) -> PowerCalculationWorker:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param worker_name:
        """

        worker: PowerCalculationWorker = WorkerResolver._load(
            worker_name, params=params, extra_dir=path
        )

        return worker

    @staticmethod
    def validate_generator(worker: PowerCalculationWorker) -> PowerCalculationWorker:
        # Validation can be added
        return worker

    @staticmethod
    def _load(
        worker_name: str,
        params: Optional[dict[str, Any]],
        extra_dir: Optional[str] = None,
    ) -> PowerCalculationWorker:
        """
        Search and loads the specified strategy.
        :param worker_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = WorkerResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_WORKERS, extra_dirs=extra_dirs
        )
        # TODO: 'E:/Documents/Projects/PySATL/pysatl-experiment/tests/resolvers/generator_path')

        worker = WorkerResolver._load_object(
            paths=abs_paths,
            object_name=worker_name,
            add_source=True,
            kwargs=params,
        )

        if not worker:
            worker = WorkerResolver._load_modules_object(object_name=worker_name, kwargs=params)

        if worker:
            return WorkerResolver.validate_generator(worker)

        raise OperationalException(
            f"Impossible to load RVS generator '{worker_name}'. This class does not exist "
            "or contains Python code errors."
        )


# TODO: support for TestWorker
