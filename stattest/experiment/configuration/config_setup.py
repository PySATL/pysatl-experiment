import logging
from typing import Any

from .config_validation import validate_config_consistency
from .load_config import load_from_files

logger = logging.getLogger(__name__)


def setup_utils_configuration(files: list[str]) -> dict[str, Any]:
    """
    Prepare the configuration for utils subcommands
    :param files:
    :return: Configuration
    """
    config = load_from_files(files)
    validate_config_consistency(config, preliminary=True)

    return config
