# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom RVS generators
"""

import logging
from typing import Any

from pysatl_experiment.constants import USERPATH_GENERATORS
from pysatl_experiment.exceptions import OperationalException
from pysatl_experiment.experiment.hypothesis import AbstractHypothesis
from pysatl_experiment.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class HypothesisResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = AbstractHypothesis
    object_type_str = "AbstractHypothesis"
    user_subdir = USERPATH_GENERATORS
    initial_search_path = None
    extra_path = "hypothesis_path"
    module_name = "pysatl_experiment.experiment.hypothesis"

    @staticmethod
    def load_hypothesis(
        hypothesis_name: str, path: str | None = None, params: dict[str, Any] | None = None
    ) -> AbstractHypothesis:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param hypothesis_name:
        """

        hypothesis: AbstractHypothesis = HypothesisResolver._load_hypothesis(
            hypothesis_name, params=params, extra_dir=path
        )

        return hypothesis

    @staticmethod
    def validate_hypothesis(generator: AbstractHypothesis) -> AbstractHypothesis:
        # Validation can be added
        return generator

    @staticmethod
    def _load_hypothesis(
        hypothesis_name: str,
        params: dict[str, Any] | None,
        extra_dir: str | None = None,
    ) -> AbstractHypothesis:
        """
        Search and loads the specified strategy.
        :param hypothesis_name: name of the module to import
        :param config: configuration for the strategy
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = HypothesisResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_GENERATORS, extra_dirs=extra_dirs
        )

        hypothesis = HypothesisResolver._load_object(
            paths=abs_paths,
            object_name=hypothesis_name,
            add_source=True,
            kwargs=params,
        )

        if not hypothesis:
            hypothesis = HypothesisResolver._load_module_object(
                object_name=hypothesis_name, kwargs=params, module_name=""
            )

        if hypothesis:
            return HypothesisResolver.validate_hypothesis(hypothesis)

        raise OperationalException(
            f"Impossible to load RVS hypothesis '{hypothesis_name}'. This class does not exist "
            "or contains Python code errors."
        )
