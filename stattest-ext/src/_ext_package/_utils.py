def _scale_sample(sample):
    """
    Scales the sample data.

    Parameters
    ----------
    sample : array_like
        Array of sample data.
    Returns
    -------
    sample_copy : array_like
        Scaled sample.
    """
    n = len(sample)
    sample_copy = sample.copy()
    sample_avg = sum(sample) / n
    for i in range(n):
        sample_copy[i] = sample_copy[i] / sample_avg

    return sample_copy


def _check_sample_length(sample):
    """
    Checks if sample length is less than 3.
    If so, ValueError is called.

    Parameters
    ----------
    sample : array_like
        Array of sample data.

    Returns
    -------
    True
    """
    n = len(sample)
    if n < 3:
        raise ValueError("Data must be at least length 3.")

    return True
