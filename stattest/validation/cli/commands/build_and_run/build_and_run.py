from click import ClickException


def validate_build_and_run(experiment_config: dict) -> None:
    """
    Validate build and run command.

    :param experiment_config: experiment configuration.
    """

    base_required_parameters = [
        "experiment_type",
        "storage_connection",
        "hypothesis",
        "sample_sizes",
        "monte_carlo_count",
    ]
    _check_required_parameters(experiment_config, base_required_parameters)

    if experiment_config.get("experiment_type") == "power":
        power_required_parameters = ["significance_levels", "alternatives"]
        _check_required_parameters(experiment_config, power_required_parameters)
    elif experiment_config.get("experiment_type") == "critical_value":
        critical_value_required_parameters = ["significance_levels"]
        _check_required_parameters(experiment_config, critical_value_required_parameters)


def _check_required_parameters(experiment_config: dict, required_parameters: list[str]) -> None:
    """
    Check if experiment configuration contains all required parameters.

    :param experiment_config: experiment configuration.
    :param required_parameters: required parameters.
    """

    missing_parameters = []

    for parameter in required_parameters:
        if parameter not in experiment_config:
            missing_parameters.append(parameter)

    is_need_to_configure = len(missing_parameters) > 0
    if is_need_to_configure:
        _raise_missing_parameters_exception(missing_parameters)


def _raise_missing_parameters_exception(missing_parameters: list[str]) -> None:
    """
    Raise exception with missing parameters.

    :param missing_parameters: missing parameters.
    """
    raise ClickException(
        f"Experiment configuration is missing required parameters: {missing_parameters}."
    )
