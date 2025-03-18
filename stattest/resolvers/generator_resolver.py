# pragma pylint: disable=attribute-defined-outside-init

"""
This module load custom RVS generators
"""

import logging
from typing import Any

from stattest.constants import USERPATH_GENERATORS, Config
from stattest.exceptions import OperationalException
from stattest.experiment.generator import AbstractRVSGenerator
from stattest.resolvers.iresolver import IResolver


logger = logging.getLogger(__name__)


class GeneratorResolver(IResolver):
    """
    This class contains the logic to load custom RVS generator class
    """

    object_type = AbstractRVSGenerator
    object_type_str = "AbstractRVSGenerator"
    user_subdir = USERPATH_GENERATORS
    initial_search_path = None
    extra_path = "generator_path"
    module_names = ["stattest.experiment.generator"]

    @staticmethod
    def load_from_config(config: Config | None) -> list[AbstractRVSGenerator]:
        if not config:
            raise OperationalException("No configuration set. Please specify configuration.")

        if not config.get("alternatives_configuration"):
            raise OperationalException("No alternatives configuration set.")

        alternatives_configuration = config["alternatives_configuration"]
        if not alternatives_configuration.get("alternatives"):
            raise OperationalException("No alternatives set.")

        alternatives = alternatives_configuration["alternatives"]
        generators = []
        for generator_conf in alternatives:
            generator = GeneratorResolver.load(generator_conf["name"], generator_conf["params"])
            generators.append(generator)

        return generators

    @staticmethod
    def load(
        name: str, path: str | None = None, params: dict[str, Any] | None = None
    ) -> AbstractRVSGenerator:
        """
        Load the custom class from config parameter
        :param params:
        :param path:
        :param name:
        """

        generator: AbstractRVSGenerator = GeneratorResolver._load(
            name, params=params, extra_dir=path
        )

        return generator

    @staticmethod
    def validate(generator: AbstractRVSGenerator) -> AbstractRVSGenerator:
        # Validation can be added
        return generator

    @staticmethod
    def _load(
        generator_name: str,
        params: dict[str, Any] | None,
        extra_dir: str | None = None,
    ) -> AbstractRVSGenerator:
        """
        Search and loads the specified strategy.
        :param generator_name: name of the module to import
        :param extra_dir: additional directory to search for the given strategy
        :return: Strategy instance or None
        """
        extra_dirs = []

        if extra_dir:
            extra_dirs.append(extra_dir)

        abs_paths = GeneratorResolver.build_search_paths(
            user_data_dir=None, user_subdir=USERPATH_GENERATORS, extra_dirs=extra_dirs
        )

        generator = GeneratorResolver._load_object(
            paths=abs_paths,
            object_name=generator_name,
            add_source=True,
            kwargs=params,
        )

        if not generator:
            generator = GeneratorResolver._load_modules_object(
                object_name=generator_name, kwargs=params
            )

        if generator:
            return GeneratorResolver.validate(generator)

        raise OperationalException(
            f"Impossible to load RVS generator '{generator_name}'. This class does not exist "
            "or contains Python code errors."
        )
