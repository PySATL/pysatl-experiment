"""An extension can provide generation tasks unrelated to GenerationData."""

from unittest.mock import Mock

from pysatl_experiment.configuration import CriticalValueExperimentConfig
from pysatl_experiment.experiment_execution.experiment_factory import AbstractExperimentFactory
from pysatl_experiment.experiment_execution.experiment_storages import ExperimentStorages
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.contracts.time_complexity import ITimeComplexityStorage


class CustomGenerationStep(IExperimentStep):
    def __init__(self, tasks: list[str]):
        self.tasks = tasks
        self.completed: list[str] = []

    def run(self) -> None:
        self.completed.extend(self.tasks)


class CustomGenerationFactory(
    AbstractExperimentFactory[
        CriticalValueExperimentConfig,
        CustomGenerationStep,
        CustomGenerationStep,
        CustomGenerationStep,
        ITimeComplexityStorage,
        str,
        int,
    ]
):
    def _create_generation_step(self, data_storage: IRandomValuesStorage, tasks: list[str]) -> CustomGenerationStep:
        return CustomGenerationStep(tasks)

    def _create_execution_step(
        self,
        data_storage: IRandomValuesStorage,
        result_storage: ITimeComplexityStorage,
        step_config: list[int],
    ) -> CustomGenerationStep:
        return CustomGenerationStep([str(task) for task in step_config])

    def _create_report_building_step(self, result_storage: ITimeComplexityStorage) -> CustomGenerationStep:
        return CustomGenerationStep([])

    def _init_result_storage(self) -> ITimeComplexityStorage:
        raise NotImplementedError("This test supplies initialized stores directly")


def test_factory_passes_custom_generation_tasks_without_conversion(make_config):
    config = make_config("critical_value")
    tasks = ["custom source A", "custom source B"]
    plan: ExperimentTaskPlan[str, int] = ExperimentTaskPlan(generation=tasks, execution=[42])
    stores = ExperimentStorages(data=Mock(), result=Mock(), experiment=Mock())
    steps = CustomGenerationFactory().create_experiment_steps(
        config, stores, ExperimentRunState(config.experiment_name, False, False), plan
    )
    assert isinstance(steps.generation_step, CustomGenerationStep)
    assert steps.generation_step.tasks is tasks
    steps.generation_step.run()
    assert steps.generation_step.completed == tasks
    assert stores.data.mock_calls == []
