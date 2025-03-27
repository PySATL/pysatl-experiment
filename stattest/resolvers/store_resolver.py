# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom RVS stores
"""

import logging
from typing import Any

from stattest.constants import USERPATH_STORES
from stattest.exceptions import OperationalException
from stattest.persistence import IStore
from stattest.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class StoreResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = IStore
    object_type_str = "IStore"
    user_subdir = USERPATH_STORES
    initial_search_path = None
    extra_path = "store_path"
    module_names = ["stattest.persistence"]

    @staticmethod
    def load(name: str, path: str | None = None, params: dict[str, Any] | None = None) -> IStore:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param name:
        """

        store: IStore = StoreResolver._load(name, params=params, extra_dir=path)

        return store

    @staticmethod
    def validate(store: IStore) -> IStore:
        # Validation can be added
        return store

    @staticmethod
    def _load(
        store_name: str,
        params: dict[str, Any] | None,
        extra_dir: str | None = None,
    ) -> IStore:
        """
        Search and loads the specified strategy.
        :param store_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = StoreResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_STORES, extra_dirs=extra_dirs
        )

        store = StoreResolver._load_object(
            paths=abs_paths,
            object_name=store_name,
            add_source=True,
            kwargs=params,
        )

        if not store:
            store = StoreResolver._load_modules_object(object_name=store_name, kwargs=params)

        if store:
            return StoreResolver.validate(store)

        raise OperationalException(
            f"Impossible to load RVS generator '{store_name}'. This class does not exist "
            "or contains Python code errors."
        )
