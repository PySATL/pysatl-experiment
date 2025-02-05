from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    AlternativeConfiguration,
    ExperimentConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.experiment.generator import BetaRVSGenerator, WeibullGenerator, symmetric_generators
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
from stattest.test import KSWeibullTest


if __name__ == "__main__":
    print("Start Weibull experiment")

    # Configuring experiment
    test_data_tel = TimeEstimationListener()

    generate_data_tel = TimeEstimationListener()
    listeners = [generate_data_tel]
    sizes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
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

    alternatives_configuration = AlternativeConfiguration(
        symmetric_generators, sizes, count=1_000, threads=3, listeners=listeners
    )

    tests = [KSWeibullTest()]
    critical_value_store = CriticalValueDbStore()
    power_calculation_worker = PowerCalculationWorker(
        0.05, 1_000_000, critical_value_store, hypothesis=WeibullHypothesis()
    )
    hypothesis = WeibullHypothesis()
    test_configuration = TestConfiguration(
        tests,
        threads=1,
        hypothesis=hypothesis,
        worker=power_calculation_worker,
        listeners=[test_data_tel],
    )

    report_builder = PdfPowerReportBuilder()
    report_configuration = ReportConfiguration(report_builder)

    rvs_store = RvsDbStore()
    result_store = ResultDbStore()
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
