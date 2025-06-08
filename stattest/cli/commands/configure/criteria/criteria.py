from click import ClickException, Context, argument, echo, pass_context

from stattest.cli.commands.common.common import (
    get_experiment_name_and_config,
    save_experiment_config,
)
from stattest.cli.commands.configure.configure import configure
from stattest.validation.cli.commands.configure.criteria.criteria import validate_criteria


@configure.command()
@argument("criteria_codes", nargs=-1)
@pass_context
def criteria(ctx: Context, criteria_codes: tuple[str, ...]) -> None:
    """
    Configure experiment criteria.

    :param ctx: context.
    :param criteria_codes: criteria codes.
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_hypothesis = experiment_config.get("hypothesis")
    if experiment_hypothesis is None:
        raise ClickException(
            f"Hypothesis is not configured.\n"
            f"Please, configure it first by calling "
            f"'experiment configure {experiment_name} hypothesis <hypothesis>'."
        )

    criteria_codes_upper = [code.upper() for code in criteria_codes]
    validate_criteria(criteria_codes_upper, experiment_hypothesis)

    criteria_data = _criteria_from_codes(criteria_codes_upper)

    experiment_config["criteria"] = criteria_data

    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Criteria of the experiment '{experiment_name}' are set to {criteria_codes_upper}.")


def _criteria_from_codes(codes: list[str]) -> list[dict]:
    """
    Convert criteria codes to criteria.

    :param codes: criteria codes.

    :return: criteria.
    """

    criteria_data = []
    for code in codes:
        criterion = {"criterion_code": code, "parameters": []}
        criteria_data.append(criterion)

    return criteria_data
