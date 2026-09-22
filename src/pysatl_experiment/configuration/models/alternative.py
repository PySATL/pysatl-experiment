"""Alternative distribution model."""

from dataclasses import dataclass

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.parameters import NumericParameters


@dataclass
class Alternative:
    """
    Alternative distribution configuration.

    Attributes
    ----------
    distribution_type : str
        Alternative distribution generator identifier.
    parameters : NumericParameters
        Generator-specific numeric parameters.
    """

    parameters: NumericParameters
    distribution_type: DistributionType

    # TODO: the `distribution_type` property was removed here — it shadowed the dataclass field
    #  of the same name (making the generated __init__ raise AttributeError: property has no setter).
    #  Keep the plain field `distribution_type: DistributionType` per the refactor intent.
