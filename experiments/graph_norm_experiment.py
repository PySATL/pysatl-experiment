import multiprocessing

from numpy import random as rd
from pysatl.criterion.normal import (
    GraphEdgesNumberNormalityGofStatistic,
    GraphMaxDegreeNormalityGofStatistic,
    KolmogorovSmirnovNormalityGofStatistic,
)

from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    ExperimentConfiguration,
    GeneratorConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.experiment.generator.generators import (
    Chi2Generator,
    ExponentialGenerator,
    GammaGenerator,
    LaplaceRVSGenerator,
    WeibullGenerator,
)
from stattest.experiment.hypothesis import NormalHypothesis
from stattest.experiment.listener.listeners import TimeEstimationListener
from stattest.experiment.report.builders import PdfPowerReportBuilder
from stattest.experiment.test.worker import PowerCalculationWorker
from stattest.persistence.db_store import CriticalValueDbStore, ResultDbStore, RvsDbStore


if __name__ == "__main__":
    print("Start graph normal experiment")

    # Configuring experiment
    test_data_tel = TimeEstimationListener()
    generate_data_tel = TimeEstimationListener()

    db_url = "sqlite:///graph_norm_experiment_two_sided.sqlite"
    listeners = [generate_data_tel]
    hypothesis = NormalHypothesis(rd.random() * 10, rd.random() * 30)
    test_threads = multiprocessing.cpu_count()
    generation_threads = multiprocessing.cpu_count()
    sizes = [10, 20, 30, 40, 50]

    critical_value_store = CriticalValueDbStore(db_url=db_url)
    rvs_store = RvsDbStore(db_url=db_url)
    result_store = ResultDbStore(db_url=db_url)

    alternatives = [
        GammaGenerator(alfa=1, beta=2),
        GammaGenerator(alfa=0.5, beta=1),
        ExponentialGenerator(2),
        WeibullGenerator(a=1, k=2),
        Chi2Generator(df=5),
        LaplaceRVSGenerator(t=0, s=1),
    ]

    edges_two_tailed = GraphEdgesNumberNormalityGofStatistic()
    edges_two_tailed.two_tailed = True

    max_degree_two_tailed = GraphMaxDegreeNormalityGofStatistic()
    max_degree_two_tailed.two_tailed = True

    tests = [
        edges_two_tailed,
        max_degree_two_tailed,
        KolmogorovSmirnovNormalityGofStatistic(),
    ]

    alternatives_configuration = GeneratorConfiguration(
        alternatives, sizes, count=1_000, threads=generation_threads, listeners=listeners
    )

    power_calculation_worker = PowerCalculationWorker(
        0.05, 1_000_000, critical_value_store, hypothesis=hypothesis
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
