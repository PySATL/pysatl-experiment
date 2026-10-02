"""Helpers for experiment names."""


def normalize_experiment_name(experiment_name: str) -> str:
    """
    Strip the ``.json`` extension from an experiment name if present.

    Parameters
    ----------
    experiment_name : str
        Experiment name, optionally ending with ``.json``.

    Returns
    -------
    str
        Normalized experiment name without the ``.json`` extension.

    Notes
    -----
    This prevents the 'name.json.json' issue when names are passed with
    or without the extension.
    """
    if experiment_name.endswith(".json"):
        return experiment_name[:-5]
    return experiment_name
