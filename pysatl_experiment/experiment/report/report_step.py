from pysatl_experiment.experiment.report.model import ResultReader
from pysatl_experiment.persistence.models import IResultStore


def execute_report_step(configuration, result_store: IResultStore):
    data_reader = ResultReader(result_store)
    # Execute before all listeners
    for listener in configuration.listeners:
        listener.before()

    # Process data
    report_builder = configuration.report_builder
    for data in data_reader:
        report_builder.process(data)

    # Build report
    report_builder.build()

    # Execute after all listeners
    for listener in configuration.listeners:
        listener.after()
