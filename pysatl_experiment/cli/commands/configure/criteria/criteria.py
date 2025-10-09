from click import BadParameter, ClickException, Context, argument, echo, pass_context
from pydantic import ValidationError

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.validation.cli.schemas.criteria import CriteriaConfig


@configure.command()
@argument("criteria_codes", nargs=-1, required=True)
@pass_context
def criteria(ctx: Context, criteria_codes: tuple[str, ...]) -> None:
    """
    Configure experiment criteria.

    Validates that the provided criteria are compatible with the
    already configured experiment hypothesis.

    :param ctx: context.
    :param criteria_codes: A list of criteria short codes (e.g., "KS", "AD").
    """
    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    experiment_hypothesis = experiment_config.get("hypothesis")
    if experiment_hypothesis is None:
        raise ClickException(
            f"Hypothesis is not configured.\n"
            f"Please, configure it first by calling "
            f"'experiment configure {experiment_name} hypothesis <hypothesis>'."
        )

    criteria_as_dicts = [{"criterion_code": code} for code in criteria_codes]
    data_to_validate = {
        "hypothesis": experiment_hypothesis,
        "criteria": criteria_as_dicts,
    }

    try:
        config = CriteriaConfig.model_validate(data_to_validate)

    except ValidationError as e:
        error_messages = [error["msg"] for error in e.errors()]
        combined_message = "\n".join(error_messages)
        raise BadParameter(combined_message)

    validated_criteria_list = [c.model_dump() for c in config.criteria]
    experiment_config["criteria"] = validated_criteria_list

    save_experiment_config(ctx, experiment_name, experiment_config)

    validated_codes = [c.criterion_code for c in config.criteria]
    echo(f"Criteria for experiment '{experiment_name}' successfully set: {validated_codes}.")
