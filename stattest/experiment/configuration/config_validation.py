import logging
from copy import deepcopy
from typing import Any

from jsonschema import Draft4Validator, validators
from jsonschema.exceptions import ValidationError, best_match

from stattest.experiment.configuration.config_schema import CONF_SCHEMA


logger = logging.getLogger(__name__)


def _extend_validator(validator_class):
    """
    Extended validator for the Freqtrade configuration JSON Schema.
    Currently, it only handles defaults for subschemas.
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for prop, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(prop, subschema["default"])

        yield from validate_properties(validator, properties, instance, schema)

    return validators.extend(validator_class, {"properties": set_defaults})


PysatlValidator = _extend_validator(Draft4Validator)


def validate_config_schema(conf: dict[str, Any], preliminary: bool = False) -> dict[str, Any]:
    """
    Validate the configuration follow the Config Schema
    :param preliminary: preliminary
    :param conf: Config in JSON format
    :return: Returns the config if valid, otherwise throw an exception
    """
    conf_schema = deepcopy(CONF_SCHEMA)
    try:
        PysatlValidator(conf_schema).validate(conf)
        return conf
    except ValidationError as e:
        logger.critical(f"Invalid configuration. Reason: {e}")
        raise ValidationError(best_match(Draft4Validator(conf_schema).iter_errors(conf)).message)


def validate_config_consistency(conf: dict[str, Any], *, preliminary: bool = False) -> None:
    """
    Validate the configuration consistency.
    Should be run after loading both configuration and strategy,
    since strategies can set certain configuration settings too.
    :param conf: Config in JSON format
    :preliminary: TODO
    :return: Returns None if everything is ok, otherwise throw an ConfigurationError
    """

    # validate configuration before returning
    logger.info("Validating configuration ...")
    validate_config_schema(conf, preliminary=preliminary)
