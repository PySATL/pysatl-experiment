from collections.abc import Sequence

from pysatl.criterion import AbstractStatistic

from stattest.experiment.generator import AbstractRVSGenerator
from stattest.persistence import IRvsStore
from stattest.persistence.models import IResultStore


class TestWorkerResult:
    pass


class ReportBuilder:
    def process(self, data: TestWorkerResult):
        pass

    def build(self):
        pass


class StepListener:
    def before(self) -> None:
        pass

    def after(self) -> None:
        pass


class TestWorker:
    def init(self):
        pass

    def execute(
        self, test: AbstractStatistic, data: list[list[float]], code, size: int
    ) -> TestWorkerResult:
        raise NotImplementedError("Method is not implemented")

    def build_id(self, test: AbstractStatistic, data: list[list[float]], code, size: int) -> str:
        raise NotImplementedError("Method is not implemented")


class ReportConfiguration:
    def __init__(
        self, report_builder: ReportBuilder, listeners: Sequence[StepListener] | None = None
    ):
        """
        Report configuration provides configuration for report.

        :param report_builder: type of report or ReportBuilder
        """
        if listeners is None:
            listeners = []
        self.report_builder = report_builder
        self.listeners = listeners


class AlternativeConfiguration:
    def __init__(
        self,
        alternatives: Sequence[AbstractRVSGenerator],
        sizes: Sequence[int],
        count=1_000,
        threads=4,
        skip_if_exists: bool = True,
        clear_before: bool = False,
        skip_step: bool = False,
        show_progress: bool = False,
        listeners: Sequence[StepListener] | None = None,
    ):
        if listeners is None:
            listeners = []
        self.alternatives = alternatives
        self.sizes = sizes
        self.count = count
        self.threads = threads
        self.skip_step = skip_step
        self.skip_if_exists = skip_if_exists
        self.clear_before = clear_before
        self.listeners = listeners
        self.show_progress = show_progress


class TestConfiguration:
    __test__ = False

    def __init__(
        self,
        tests: Sequence[AbstractStatistic],
        worker: TestWorker,
        threads=4,
        listeners: Sequence[StepListener] | None = None,
        skip_step: bool = False,
    ):
        if listeners is None:
            listeners = []
        self.tests = tests
        self.threads = threads
        self.listeners = listeners
        self.worker = worker
        self.skip_step = skip_step


class ExperimentConfiguration:
    def __init__(
        self,
        alternative_configuration: AlternativeConfiguration,
        test_configuration: TestConfiguration,
        report_configuration: ReportConfiguration,
        rvs_store: IRvsStore,
        result_store: IResultStore,
    ):
        self.alternative_configuration = alternative_configuration
        self.test_configuration = test_configuration
        self.report_configuration = report_configuration
        self.rvs_store = rvs_store
        self.result_store = result_store
