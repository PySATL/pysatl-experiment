from click import BadParameter, Context, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import (
    criteria_from_codes,
    get_experiment_name_and_config,
    get_statistics_short_codes_for_hypothesis,
    save_experiment_config,
)
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


@configure.command()
@argument("hyp")
@pass_context
def hypothesis(ctx: Context, hyp: str) -> None:
    """
    Set the statistical hypothesis for the current experiment.

    This command configures the main statistical hypothesis to be tested,
    such as 'normal'.

    IMPORTANT: Setting a hypothesis will automatically overwrite the existing
    list of criteria with all criteria compatible with that hypothesis.

    Example:
        experiment configure MyNormalTest hypothesis normal

    Args:
        ctx: The Click context object, passed automatically.
     hyp: The desired hypothesis (e.g., 'normal'). The value must
            match one of the predefined types in `Hypothesis` and is
            case-insensitive.
    """
    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    try:
        validated_hypothesis = Hypothesis(hyp.lower())
    except ValueError:
        valid_options = [e.value for e in Hypothesis]
        raise BadParameter(f"Type of '{hyp}' is not valid.\nPossible values are: {valid_options}.")

    experiment_config["hypothesis"] = validated_hypothesis.value

    criteria_for_hypothesis = get_statistics_short_codes_for_hypothesis(validated_hypothesis.value)
    criteria_data = criteria_from_codes(criteria_for_hypothesis)
    experiment_config["criteria"] = criteria_data

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(
        f"Hypothesis of the experiment '{experiment_name}' is set to '{validated_hypothesis}'.\n"
        f"Likewise, all criteria for the hypothesis '{validated_hypothesis.value}' are set."
    )
