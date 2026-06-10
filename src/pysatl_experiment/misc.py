"""Core utilities for PySatl experiment system."""


def deep_merge_dicts(source, destination, allow_null_overrides: bool = True):
    """
    Deep merge two dictionaries in-place.

    Parameters
    ----------
    source : dict
        Source dictionary whose values override destination.
    destination : dict
        Target dictionary modified in-place.
    allow_null_overrides : bool, optional
        If True, None values from source override destination values.

    Returns
    -------
    dict
        Merged destination dictionary.

    Sample
    ------
    >>> a = { 'first' : { 'rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }

    Notes
    -----
    Values from Source override destination, destination is returned (and modified!!).
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            deep_merge_dicts(value, node, allow_null_overrides)
        elif value is not None or allow_null_overrides:
            destination[key] = value

    return destination
