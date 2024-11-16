from matplotlib import pyplot as plt

from stattest.experiment import ReportBuilder
from stattest.experiment.test.worker import PowerWorkerResult
from stattest.persistence.sql_lite_store.power_result_store import PowerResultSqlLiteStore


class ChartPowerReportBuilder(ReportBuilder):
    def __init__(self):
        self.data = {}

    def process(self, result: PowerWorkerResult):
        key = ChartPowerReportBuilder.__build_path(result)
        point = (result.size, result.power)
        if key in self.data.keys():
            self.data[key].append(point)
        else:
            self.data[key] = [point]

    def build(self):
        for key in self.data:
            value = self.data[key]
            sorted_value = sorted(value, key=lambda tup: tup[0])
            s = [x[0] for x in sorted_value]
            p = [x[1] for x in sorted_value]

            fig, ax = plt.subplots()
            ax.plot(s, p)

            ax.set(xlabel='time (s)', ylabel='voltage (mV)',
                   title='About as simple as it gets, folks')
            ax.grid()

            fig.savefig("test.png")
            plt.show()

    @staticmethod
    def __build_path(result: PowerWorkerResult):
        return '_'.join([result.test_code, str(result.alternative_code), str(result.alpha)])


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
