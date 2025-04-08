import multiprocessing

from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    AlternativeConfiguration,
    ExperimentConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.experiment.generator import WeibullGenerator, BetaRVSGenerator, CauchyRVSGenerator, LaplaceRVSGenerator, \
    LogisticRVSGenerator, TRVSGenerator, TukeyRVSGenerator, symmetric_generators, asymmetric_generators
from stattest.experiment.generator.generators import (
    ExponentialGenerator,
    GammaGenerator,
    GompertzGenerator,
    InvGaussGenerator,
    LognormGenerator,
    RiceGenerator, NormalRVSGenerator,
)
from stattest.experiment.hypothesis.hypothesis import ExponentialHypothesis
from stattest.experiment.listener.listeners import TimeEstimationListener
from stattest.experiment.report.model import PdfPowerReportBuilder
from stattest.experiment.test.worker import PowerCalculationWorker
from stattest.persistence.db_store import CriticalValueDbStore, RvsDbStore
from stattest.persistence.db_store.result_store import ResultDbStore
from stattest.test import (
    EPTestExp,
    KSTestExp,
    AHSTestExp,
    ATKTestExp,
    COTestExp,
    CVMTestExp,
    DSPTestExp,
    EPSTestExp,
    FZTestExp,
    GiniTestExp,
    GDTestExp,
    HMTestExp,
    HG1TestExp,
    HG2TestExp,
    HPTestExp,
    KMTestExp,
    KCTestExp,
    LZTestExp,
    MNTestExp,
    PTTestExp,
    SWTestExp,
    RSTestExp,
    WETestExp,
    WWTestExp,

)


if __name__ == "__main__":
    print("Start Exponential experiment")

    # Configuring experiment
    test_data_tel = TimeEstimationListener()
    generate_data_tel = TimeEstimationListener()

    cv_db_url = "sqlite:///exponential_experiment_cv.sqlite"
    rvs_db_url = "sqlite:///exponential_experiment_rvs.sqlite"
    result_db_url = "sqlite:///exponential_experiment_result.sqlite"

    db_url = "sqlite:///exponential_experiment.sqlite"

    listeners = [generate_data_tel]
    hypothesis = ExponentialHypothesis()
    test_threads = multiprocessing.cpu_count()
    generation_threads = 4
    sizes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

    critical_value_store = CriticalValueDbStore(db_url=cv_db_url)
    rvs_store = RvsDbStore(db_url=db_url)
    result_store = ResultDbStore(db_url=result_db_url)

    alternatives = symmetric_generators + asymmetric_generators

    tests = [
        EPTestExp(),
        KSTestExp(),
        ATKTestExp(),
        COTestExp(),
        CVMTestExp(),
        DSPTestExp(),
        EPSTestExp(),
        FZTestExp(),
        GiniTestExp(),
        GDTestExp(),
        HMTestExp(),
        HG1TestExp(),
        HG2TestExp(),
        KMTestExp(),
        KCTestExp(),
        LZTestExp(),
        MNTestExp(),
        PTTestExp(),
        SWTestExp(),
        WETestExp(),
        WWTestExp(),
        # HPTestExp(),
        # AHSTestExp(),
        # RSTestExp()
    ]

    alternatives_configuration = AlternativeConfiguration(
        alternatives, sizes, count=1_000, threads=generation_threads, listeners=listeners
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
