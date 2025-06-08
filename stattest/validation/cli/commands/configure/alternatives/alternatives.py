import inspect

from click import BadParameter

from stattest.experiment.generator import AbstractRVSGenerator


def validate_alternatives(alternatives: tuple[str], experiment_type: str) -> list[dict]:
    """
    Validate experiment alternatives.

    :param alternatives: alternatives.
    :param experiment_type: experiment type.
    """
    if experiment_type != "power":
        raise BadParameter(
            f"Alternatives are not supported for the experiment type '{experiment_type}'."
        )

    parsed = []

    generator_by_name = {cls.__name__.upper(): cls for cls in AbstractRVSGenerator.__subclasses__()}

    for alt_str in alternatives:
        generator_name, parameters = _parse_alternative(alt_str)
        generator_name_upper = generator_name.upper()

        param_names, param_count = _get_generator_parameter_names_and_count(
            generator_name, generator_by_name
        )

        if len(parameters) != param_count:
            raise BadParameter(
                f"Generator '{generator_name}' needs {param_count} parameters, got {len(parameters)}."
            )

        alternative_data = {"generator_name": generator_name_upper, "parameters": parameters}

        parsed.append(alternative_data)

    return parsed


def _parse_alternative(alternative: str) -> tuple[str, list[float]]:
    """
    Parse alternative.

    :param alternative: alternative.
    """

    parts = alternative.split()
    generator_name = parts[0]

    try:
        parameters = [float(v) for v in parts[1:]]
    except ValueError:
        raise BadParameter(f"Parameters for generator '{generator_name}' must be floats.")

    return generator_name, parameters


def _get_generator_parameter_names_and_count(
    generator_name: str, generator_by_name: dict[str, type[AbstractRVSGenerator]]
) -> tuple[list[str], int]:
    """
    Get generator parameter names and count.

    :param generator_name: generator name.
    :param generator_by_name: generator by name dictionary.
    """

    cls = generator_by_name.get(generator_name)
    if not cls:
        raise BadParameter(f"Generator '{generator_name}' is not found.")

    sig = inspect.signature(cls.__init__)
    param_names = [
        p.name
        for p in sig.parameters.values()
        if p.name != "self" and p.kind == p.POSITIONAL_OR_KEYWORD
    ]
    param_count = len(param_names)

    return param_names, param_count
