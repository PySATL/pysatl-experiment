from stattest.experiment.generator import AbstractRVSGenerator
from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.persistence import IRvsStore, ICriticalValueStore
from stattest.test import AbstractTestStatistic


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
    def execute(self, test: AbstractTestStatistic, data: [[float]], code, size: int) -> TestWorkerResult:
        pass

    def save_result(self, result: TestWorkerResult):
        pass


class ReportConfiguration:
    def __init__(self, report_builder: ReportBuilder, data_reader, listeners: [StepListener] = None):
        """
        Report configuration provides configuration for report.

        :param report_builder: type of report or ReportBuilder
        """
        if listeners is None:
            listeners = []
        self.report_builder = report_builder
        self.listeners = listeners
        self.data_reader = data_reader


class AlternativeConfiguration:
    def __init__(self, alternatives: [AbstractRVSGenerator], sizes: [int], count=1_000, threads=4,
                 skip_if_exists: bool = True,
                 clear_before: bool = False,
                 skip_step: bool = False,
                 show_progress: bool = False,
                 listeners: [StepListener] = None,
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
    def __init__(self, tests: [AbstractTestStatistic], worker: TestWorker, hypothesis: AbstractHypothesis, threads=4,
                 listeners: [StepListener] = None, skip_step: bool = False, ):
        if listeners is None:
            listeners = []
        self.tests = tests
        self.threads = threads
        self.listeners = listeners
        self.worker = worker
        self.hypothesis = hypothesis
        self.skip_step = skip_step


class ExperimentConfiguration:
    def __init__(self,
                 alternative_configuration: AlternativeConfiguration,
                 test_configuration: TestConfiguration,
                 report_configuration: ReportConfiguration,
                 rvs_store: IRvsStore,
                 critical_value_store: ICriticalValueStore):
        self.alternative_configuration = alternative_configuration
        self.test_configuration = test_configuration
        self.report_configuration = report_configuration
        self.rvs_store = rvs_store
        self.critical_value_store = critical_value_store
