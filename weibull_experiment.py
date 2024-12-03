from stattest.experiment.experiment import Experiment
from stattest.experiment.configuration.configuration import TestConfiguration, AlternativeConfiguration, ExperimentConfiguration, ReportConfiguration
from stattest.experiment.generator import BetaRVSGenerator, symmetric_generators
from stattest.experiment.hypothesis import WeibullHypothesis
from stattest.experiment.listener.listeners import TimeEstimationListener
from stattest.experiment.report.model import PdfPowerReportBuilder
from stattest.experiment.test.worker import PowerCalculationWorker
from stattest.persistence.sql_lite_store import (
    CriticalValueSqLiteStore,
    ResultSqLiteStore,
    RvsSqLiteStore,
)
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
    critical_value_store = CriticalValueSqLiteStore()
    power_result_store = ResultSqLiteStore()
    power_calculation_worker = PowerCalculationWorker(
        0.05, 1_000_000, power_result_store, critical_value_store, hypothesis=WeibullHypothesis()
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

    rvs_store = RvsSqLiteStore()
    experiment_configuration = ExperimentConfiguration(
        alternatives_configuration,
        test_configuration,
        report_configuration,
        rvs_store=rvs_store,
        critical_value_store=CriticalValueSqLiteStore(),
    )
    experiment = Experiment(experiment_configuration)

    # Execute experiment
    experiment.execute()
