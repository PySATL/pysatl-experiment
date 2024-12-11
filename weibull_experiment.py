from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    AlternativeConfiguration,
    ExperimentConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.experiment.generator import BetaRVSGenerator, symmetric_generators
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
    sizes = [1000, 100, 10]
    alternatives = [BetaRVSGenerator(a=0.5, b=0.5)]

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
        critical_value_store=CriticalValueDbStore(),
    )
    experiment = Experiment(experiment_configuration)

    # Execute experiment
    experiment.execute()
