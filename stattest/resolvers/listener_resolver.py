# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom listeners
"""

import logging
from typing import Any

from stattest.constants import USERPATH_LISTENERS
from stattest.exceptions import OperationalException
from stattest.experiment.configuration import StepListener
from stattest.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class ListenerResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = StepListener
    object_type_str = "StepListener"
    user_subdir = USERPATH_LISTENERS
    initial_search_path = None
    extra_path = "listener_path"
    module_names = ["stattest.experiment.listener"]

    @staticmethod
    def load(
        name: str, path: str | None = None, params: dict[str, Any] | None = None
    ) -> StepListener:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param name:
        """

        listener: StepListener = ListenerResolver._load(name, params=params, extra_dir=path)

        return listener

    @staticmethod
    def validate(listener: StepListener) -> StepListener:
        # Validation can be added
        return listener

    @staticmethod
    def _load(
        listener_name: str,
        params: dict[str, Any] | None,
        extra_dir: str | None = None,
    ) -> StepListener:
        """
        Search and loads the specified strategy.
        :param listener_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = ListenerResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_LISTENERS, extra_dirs=extra_dirs
        )

        listener = ListenerResolver._load_object(
            paths=abs_paths,
            object_name=listener_name,
            add_source=True,
            kwargs=params,
        )

        if not listener:
            listener = ListenerResolver._load_modules_object(
                object_name=listener_name, kwargs=params
            )

        if listener:
            return ListenerResolver.validate(listener)

        raise OperationalException(
            f"Impossible to load RVS generator '{listener_name}'. This class does not exist "
            "or contains Python code errors."
        )
