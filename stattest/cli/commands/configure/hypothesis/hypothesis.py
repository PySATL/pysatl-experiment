from click import Context, argument, echo, pass_context

from stattest.cli.commands.common.common import (
    get_experiment_name_and_config,
    get_statistics_codes_for_hypothesis,
    save_experiment_config,
)
from stattest.cli.commands.configure.configure import configure
from stattest.validation.cli.commands.configure.hypothesis.hypothesis import validate_hypothesis


@configure.command()
@argument("hyp")
@pass_context
def hypothesis(ctx: Context, hyp: str) -> None:
    """
    Configure experiment hypothesis.

    :param ctx: context.
    :param hyp: hypothesis.
    """

    validate_hypothesis(hyp)
    hyp_lower = hyp.lower()

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_config["hypothesis"] = hyp_lower

    criteria_for_hypothesis = get_statistics_codes_for_hypothesis(hyp_lower)
    experiment_config["criteria"] = criteria_for_hypothesis

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(
        f"Hypothesis of the experiment '{experiment_name}' is set to '{hyp_lower}'.\n"
        f"Likewise, all criteria for the hypothesis '{hyp_lower}' are set."
    )
