import multiprocessing

from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    AlternativeConfiguration,
    ExperimentConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.experiment.generator.generators import (
    ExponentialGenerator,
    GammaGenerator,
)
from stattest.experiment.hypothesis import NormalHypothesis
from stattest.experiment.listener.listeners import TimeEstimationListener
from stattest.experiment.report.model import PdfPowerReportBuilder
from stattest.experiment.test.worker import PowerCalculationWorker
from stattest.persistence.db_store import CriticalValueDbStore, RvsDbStore
from stattest.persistence.db_store.result_store import ResultDbStore
from stattest.test.normal import (
    CVMNormalityTest,
    DAPNormalityTest,
    GraphEdgesNumberNormTest,
    GraphMaxDegreeNormTest,
)


if __name__ == "__main__":
    print("Start graph normal experiment")

    # Configuring experiment
    test_data_tel = TimeEstimationListener()
    generate_data_tel = TimeEstimationListener()

    db_url = "sqlite:///graph_norm_experiment4.sqlite"
    listeners = [generate_data_tel]
    hypothesis = NormalHypothesis()
    test_threads = multiprocessing.cpu_count()
    generation_threads = multiprocessing.cpu_count()
    sizes = [10, 20, 50, 100, 200, 300]

    critical_value_store = CriticalValueDbStore(db_url=db_url)
    rvs_store = RvsDbStore(db_url=db_url)
    result_store = ResultDbStore(db_url=db_url)

    alternatives = [
        GammaGenerator(alfa=1, beta=2),
        GammaGenerator(alfa=2, beta=2),
        GammaGenerator(alfa=3, beta=2),
        GammaGenerator(alfa=0.5, beta=1),
        ExponentialGenerator(),
        ExponentialGenerator(1),
        ExponentialGenerator(2),
    ]
    tests = [
        GraphEdgesNumberNormTest(),
        GraphMaxDegreeNormTest(),
        CVMNormalityTest(),
        DAPNormalityTest(),
    ]

    alternatives_configuration = AlternativeConfiguration(
        alternatives, sizes, count=1_00, threads=generation_threads, listeners=listeners
    )

    power_calculation_worker = PowerCalculationWorker(
        0.05, 100_000, critical_value_store, hypothesis=hypothesis
    )
    test_configuration = TestConfiguration(
        tests,
        threads=test_threads,
        worker=power_calculation_worker,
        listeners=[test_data_tel],
    )

    report_builder = PdfPowerReportBuilder()
    report_configuration = ReportConfiguration(report_builder)

    experiment_configuration = ExperimentConfiguration(
        alternatives_configuration,
        test_configuration,
        report_configuration,
        rvs_store=rvs_store,
        result_store=result_store,
    )
    experiment = Experiment(experiment_configuration)

    # Execute experiment
    experiment.execute()
