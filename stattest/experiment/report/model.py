from stattest.experiment import ReportBuilder
from stattest.experiment.test.worker import PowerWorkerResult
from stattest.persistence.sql_lite_store.power_result_store import PowerResultSqlLiteStore


class PdfPowerReportBuilder(ReportBuilder):
    def __init__(self):
        self.data = {}

    def process(self, result: PowerWorkerResult):
        pass

    def build(self):
        pass


class PowerResultReader:
    def __init__(self, power_result_store: PowerResultSqlLiteStore, batch_size=100):
        self.power_result_store = power_result_store
        self.batch_size = batch_size
        self.offset = 0
        self.items = []
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.i += 1
        if self.i >= len(self.items):
            self.items = self.power_result_store.get_powers(offset=self.offset, limit=self.batch_size)
            self.i = 0
            self.offset += self.batch_size
            if len(self.items) == 0:
                raise StopIteration
        return self.items[self.i]
