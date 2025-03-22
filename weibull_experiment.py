import multiprocessing

from pysatl.criterion import (
    AndersonDarlingWeibullGofStatistic,
    Chi2PearsonWeibullGofStatistic,
    CrammerVonMisesWeibullGofStatistic,
    KolmogorovSmirnovWeibullGofStatistic,
    LillieforsWeibullGofStatistic,
    LOSWeibullGofStatistic,
    MinToshiyukiWeibullGofStatistic,
    MSFWeibullGofStatistic,
    OKWeibullGofStatistic,
    RSBWeibullGofStatistic,
    SBWeibullGofStatistic,
    ST1WeibullGofStatistic,
    ST2WeibullGofStatistic,
    TikuSinghWeibullGofStatistic,
)
from pysatl.criterion.weibull import (
    KullbackLeiblerWeibullGofStatistic,
    LaplaceTransform2WeibullGofStatistic,
    LaplaceTransform3WeibullGofStatistic,
    LaplaceTransformWeibullGofStatistic,
    LiaoShimokawaWeibullGofStatistic,
    MahdiDoostparastWeibullGofStatistic,
    REJGWeibullGofStatistic,
    WatsonWeibullGofStatistic,
)

from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    AlternativeConfiguration,
    ExperimentConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.experiment.generator import WeibullGenerator
from stattest.experiment.generator.generators import (
    ExponentialGenerator,
    GammaGenerator,
    GompertzGenerator,
    InvGaussGenerator,
    LognormGenerator,
    RiceGenerator,
)
from stattest.experiment.hypothesis import WeibullHypothesis
from stattest.experiment.listener.listeners import TimeEstimationListener
from stattest.experiment.report.model import PdfPowerReportBuilder
from stattest.experiment.test.worker import PowerCalculationWorker
from stattest.persistence.db_store import CriticalValueDbStore, RvsDbStore
from stattest.persistence.db_store.result_store import ResultDbStore


if __name__ == "__main__":
    print("Start Weibull experiment")

    # Configuring experiment
    test_data_tel = TimeEstimationListener()
    generate_data_tel = TimeEstimationListener()

    db_url = "sqlite:///weibull_experiment.sqlite"
    listeners = [generate_data_tel]
    hypothesis = WeibullHypothesis()
    test_threads = multiprocessing.cpu_count()
    generation_threads = multiprocessing.cpu_count()
    sizes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

    critical_value_store = CriticalValueDbStore(db_url=db_url)
    rvs_store = RvsDbStore(db_url=db_url)
    result_store = ResultDbStore(db_url=db_url)

    alternatives = [
        ExponentialGenerator(lam=0.5),
        ExponentialGenerator(lam=1),
        ExponentialGenerator(lam=1.5),
        GammaGenerator(alfa=1, beta=2),
        GammaGenerator(alfa=2, beta=2),
        GammaGenerator(alfa=3, beta=2),
        GammaGenerator(alfa=5, beta=1),
        GammaGenerator(alfa=9, beta=0.5),
        GammaGenerator(alfa=0.5, beta=1),
        InvGaussGenerator(mu=1, lam=0.2),
        InvGaussGenerator(mu=1, lam=1),
        InvGaussGenerator(mu=1, lam=3),
        InvGaussGenerator(mu=3, lam=0.2),
        InvGaussGenerator(mu=3, lam=1),
        LognormGenerator(mu=0, s=0.25),
        LognormGenerator(mu=0, s=1),
        LognormGenerator(mu=0, s=5),
        LognormGenerator(mu=5, s=0.25),
        LognormGenerator(mu=5, s=1),
        LognormGenerator(mu=5, s=5),
        RiceGenerator(nu=0, sigma=1),
        RiceGenerator(nu=0.5, sigma=1),
        RiceGenerator(nu=4, sigma=1),
        GompertzGenerator(eta=0.1, b=1),
        GompertzGenerator(eta=2, b=1),
        GompertzGenerator(eta=3, b=1),
        GompertzGenerator(eta=1, b=2),
        GompertzGenerator(eta=1, b=3),
        WeibullGenerator(l=1, k=5),
        WeibullGenerator(l=2, k=5),
    ]
    tests = [
        KolmogorovSmirnovWeibullGofStatistic(),
        MinToshiyukiWeibullGofStatistic(),
        Chi2PearsonWeibullGofStatistic(),
        CrammerVonMisesWeibullGofStatistic(),
        ST1WeibullGofStatistic(),
        ST2WeibullGofStatistic(),
        TikuSinghWeibullGofStatistic(),
        LOSWeibullGofStatistic(),
        MSFWeibullGofStatistic(),
        OKWeibullGofStatistic(),
        SBWeibullGofStatistic(),
        RSBWeibullGofStatistic(),
        LaplaceTransform3WeibullGofStatistic(),
        LaplaceTransform2WeibullGofStatistic(),
        LaplaceTransformWeibullGofStatistic(),
        KullbackLeiblerWeibullGofStatistic(),
        LiaoShimokawaWeibullGofStatistic(),
        WatsonWeibullGofStatistic(),
        MahdiDoostparastWeibullGofStatistic(),
        REJGWeibullGofStatistic(),
        AndersonDarlingWeibullGofStatistic(),
        LillieforsWeibullGofStatistic(),
    ]

    alternatives_configuration = AlternativeConfiguration(
        alternatives,
        sizes,
        count=1_000,
        threads=generation_threads,
        listeners=listeners,
        skip_step=True,
    )

    power_calculation_worker = PowerCalculationWorker(
        0.05, 100_000, critical_value_store, hypothesis=hypothesis
    )
    test_configuration = TestConfiguration(
        tests,
        threads=test_threads,
        worker=power_calculation_worker,
        listeners=[test_data_tel],
        skip_step=True,
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
