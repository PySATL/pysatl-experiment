import json

from click import BadParameter, Choice, ClickException, FloatRange, IntRange, argument, command, echo, option
from pydantic import ValidationError

from pysatl_experiment.cli.commands.common.common import (
    create_storage_path,
    criteria_from_codes,
    get_experiment_config,
    get_statistics_short_codes_for_hypothesis,
    read_experiment_data,
    save_experiment_config,
)
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.validation.cli.commands.common.common import if_experiment_exists
from pysatl_experiment.validation.cli.schemas.alternative import AlternativesConfig
from pysatl_experiment.validation.cli.schemas.criteria import CriteriaConfig


def __configure_sample_sizes(experiment_config: dict, sizes: tuple[int, ...] | None):
    if sizes is None:
        return

    sizes_list = list(sizes)
    experiment_config["sample_sizes"] = sizes_list


def __configure_run_mode(experiment_config: dict, mode: str | None):
    if mode is None:
        return

    validated_run_mode = RunMode(mode.lower())
    experiment_config["run_mode"] = validated_run_mode.value


def __configure_report_mode(experiment_config: dict, mode: str | None):
    if mode is None:
        return

    validated_report_mode = ReportMode(mode.lower())
    experiment_config["report_mode"] = validated_report_mode.value


def __configure_generator_type(experiment_config: dict, generator_type: str | None):
    if generator_type is None:
        return

    validated_step = StepType(generator_type.lower())
    if validated_step == StepType.CUSTOM:
        raise BadParameter("Custom type is not supported yet.\nPlease, choose standard one")

    gen_type_lower = generator_type.lower()
    experiment_config["generator_type"] = gen_type_lower


def __configure_criteria(experiment_config: dict, criteria: tuple[str, ...] | None):
    if criteria is None or len(criteria) == 0:
        return

    experiment_hypothesis = experiment_config.get("hypothesis")
    criteria_as_dicts = [{"criterion_code": code} for code in criteria]
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

    print([c for c in config.criteria])
    validated_criteria_list = [c.model_dump() for c in config.criteria]
    experiment_config["criteria"] = validated_criteria_list


def __configure_hypothesis(experiment_config: dict, hypothesis: str | None):
    if hypothesis is None:
        return

    validated_hypothesis = Hypothesis(hypothesis.lower())
    experiment_config["hypothesis"] = validated_hypothesis.value

    criteria_for_hypothesis = get_statistics_short_codes_for_hypothesis(validated_hypothesis.value)
    criteria_data = criteria_from_codes(criteria_for_hypothesis)
    experiment_config["criteria"] = criteria_data


def __configure_executor_type(experiment_config: dict, executor_type: str | None):
    if executor_type is None:
        return

    validated_step = StepType(executor_type.lower())
    if validated_step == StepType.CUSTOM:
        raise BadParameter("Custom type is not supported yet.\nPlease, choose standard one")

    exec_type_lower = executor_type.lower()
    experiment_config["executor_type"] = exec_type_lower


def __configure_report_builder_type(experiment_config: dict, report_build_type: str | None):
    if report_build_type is None:
        return

    validated_step = StepType(report_build_type.lower())
    if validated_step == StepType.CUSTOM:
        raise BadParameter("Custom type is not supported yet.\nPlease, choose standard one")

    report_build_type_lower = report_build_type.lower()
    experiment_config["report_builder_type"] = report_build_type_lower


def __configure_monte_carlo_count(experiment_config: dict, count: int | None):
    if count is None:
        return

    experiment_config["monte_carlo_count"] = count


def __configure_storage_connection(experiment_config: dict, connection: str):
    storage_path = create_storage_path(connection)
    experiment_config["storage_connection"] = storage_path


def __configure_experiment_type(experiment_config: dict, experiment_type: str | None):
    if experiment_type is None:
        return

    validated_experiment_type = ExperimentType(experiment_type.lower())
    experiment_config["experiment_type"] = validated_experiment_type.value


def __configure_alternatives(experiment_config: dict, alternative: tuple[str] | None):
    if alternative is None:
        return

    experiment_type = experiment_config.get("experiment_type")

    try:
        validated_config = AlternativesConfig(experiment_type=experiment_type, alternatives=list(alternative))  # type: ignore[arg-type]

        alternatives_data = validated_config.model_dump().get("alternatives", [])
    except ValidationError as e:
        error_messages = []

        for error in e.errors():
            if error["loc"] and error["loc"][0] == "alternatives":
                if len(error["loc"]) > 1:
                    index = error["loc"][1]
                    if isinstance(index, int):
                        user_input = alternative[index]
                        msg = f"For alternative #{index + 1} ('{user_input}'): {error['msg']}"
                        error_messages.append(msg)
                else:
                    error_messages.append(f"- {error['msg']}")
            else:
                field = " -> ".join(map(str, error["loc"]))
                error_messages.append(f"In field '{field}': {error['msg']}")

        final_message = "\n" + "\n".join(error_messages)

        raise ClickException(final_message)

    experiment_config["alternatives"] = alternatives_data


def __configure_significance_levels(experiment_config: dict, levels: tuple[float, ...] | None):
    if levels is None:
        return

    experiment_type = experiment_config.get("experiment_type")
    if experiment_type == "time_complexity":
        raise ClickException("Significance levels are not supported for time complexity experiments.")

    levels_list = list(levels)
    experiment_config["significance_levels"] = levels_list


@command()
@argument("name")
@option("-alt", "--alternative", multiple=True, help="Alternative generator. Example: 'generator_name param1 param2'")
@option(
    "-con",
    "--connection",
    required=True,
    help="Storage connection. Example: postgresql://postgres:postgres@localhost/pysatl",
)
@option(
    "-l",
    "--levels",
    multiple=True,
    type=FloatRange(min=0.0, max=1.0, min_open=True, max_open=True),
    help="Significant levels. Example: '0.5 0.1 0.01'",
)
@option("-s", "--size", required=True, multiple=True, type=IntRange(min=10), help="Sample sizes. Example: '10 20 30'")
@option("-rm", "--run-mode", type=Choice(RunMode.list()), help="Run mode. Example: reuse")
@option("-rp", "--report-mode", type=Choice(ReportMode.list()), help="Report type. Example: with-chart")
@option("-rbt", "--report-builder-type", type=Choice(StepType.list()), help="Report builder type. Example: standard")
@option("-c", "--count", required=True, type=IntRange(min=100), help="Montecarlo iterations count. Example: 10000")
@option(
    "-h", "--hypothesis", required=True, type=Choice(Hypothesis.list()), help="Hypothesis GoF type. Example: normal"
)
@option("-gt", "--generator-type", type=Choice(StepType.list()), help="Generator type. Example: standard")
@option(
    "-expt",
    "--experiment-type",
    required=True,
    type=Choice(ExperimentType.list()),
    help="Experiment type. Example: power",
)
@option("-et", "--executor-type", type=Choice(StepType.list()), help="Executor type. Example: standard")
@option("-cr", "--criteria", multiple=True, help="Criterion codes. Example: KS")
def configure(
    name: str,
    alternative: tuple[str],
    connection: str,
    levels: tuple[float, ...],
    size: tuple[int, ...],
    run_mode: str,
    report_mode: str,
    report_builder_type: str,
    count: int,
    hypothesis: str,
    generator_type: str,
    experiment_type: str,
    executor_type: str,
    criteria: tuple[str, ...],
) -> None:
    """
    Configure experiment parameters.

    :param name: name of the experiment.
    """

    experiment_exists = if_experiment_exists(name)
    if not experiment_exists:
        raise ClickException(f"Experiment with name {name} does not exist.")

    experiment_config = get_experiment_config(read_experiment_data(name))

    __configure_experiment_type(experiment_config, experiment_type)
    __configure_storage_connection(experiment_config, connection)
    __configure_significance_levels(experiment_config, levels)
    __configure_sample_sizes(experiment_config, size)
    __configure_run_mode(experiment_config, run_mode)
    __configure_report_mode(experiment_config, report_mode)
    __configure_report_builder_type(experiment_config, report_builder_type)
    __configure_monte_carlo_count(experiment_config, count)
    __configure_hypothesis(experiment_config, hypothesis)
    __configure_generator_type(experiment_config, generator_type)
    __configure_executor_type(experiment_config, executor_type)
    __configure_criteria(experiment_config, criteria)
    __configure_alternatives(experiment_config, alternative)

    save_experiment_config(name, experiment_config)

    echo(f"Experiment {name} successfully configured! Configuration: \n {json.dumps(experiment_config, indent=4)}")
