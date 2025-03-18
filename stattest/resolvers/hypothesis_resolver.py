# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom hypotheses
"""

import logging
from typing import Any

from stattest.constants import USERPATH_HYPOTHESIS
from stattest.exceptions import OperationalException
from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class HypothesisResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = AbstractHypothesis
    object_type_str = "AbstractHypothesis"
    user_subdir = USERPATH_HYPOTHESIS
    initial_search_path = None
    extra_path = "hypothesis_path"
    module_names = ["stattest.experiment.hypothesis"]

    @staticmethod
    def load(
        name: str, path: str | None = None, params: dict[str, Any] | None = None
    ) -> AbstractHypothesis:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param name:
        """

        hypothesis: AbstractHypothesis = HypothesisResolver._load(
            name, params=params, extra_dir=path
        )

        return hypothesis

    @staticmethod
    def validate(hypothesis: AbstractHypothesis) -> AbstractHypothesis:
        # Validation can be added
        return hypothesis

    @staticmethod
    def _load(
        hypothesis_name: str,
        params: dict[str, Any] | None,
        extra_dir: str | None = None,
    ) -> AbstractHypothesis:
        """
        Search and loads the specified strategy.
        :param hypothesis_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = HypothesisResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_HYPOTHESIS, extra_dirs=extra_dirs
        )

        hypothesis = HypothesisResolver._load_object(
            paths=abs_paths,
            object_name=hypothesis_name,
            add_source=True,
            kwargs=params,
        )

        if not hypothesis:
            hypothesis = HypothesisResolver._load_modules_object(
                object_name=hypothesis_name, kwargs=params
            )

        if hypothesis:
            return HypothesisResolver.validate(hypothesis)

        raise OperationalException(
            f"Impossible to load RVS hypothesis '{hypothesis_name}'. This class does not exist "
            "or contains Python code errors."
        )
