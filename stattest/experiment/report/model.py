from typing import Any

from stattest.persistence.models import IResultStore


"""
class ChartBenchmarkMeanReportBuilder(ReportBuilder):
    def __init__(self):
        self.data = {}
        self.sizes = set()
        self.codes = set()

    def process(self, result: BenchmarkWorkerResult):
        key = result.test_code  # ChartBenchmarkMeanReportBuilder.__build_path(result)
        point = (result.size, np.mean(result.benchmark))
        self.sizes.add(result.size)
        self.codes.add(result.test_code)
        if key in self.data.keys():
            self.data[key].append(point)
        else:
            self.data[key] = [point]

    def build(self):
        sizes = [f"{i}" for i in sorted(self.sizes)]
        x = np.arange(len(sizes))
        width = 0.1
        fig, ax = plt.subplots()
        i = 1
        for key in self.data:
            value = self.data[key]
            sorted_value = sorted(value, key=lambda tup: tup[0])
            p = [x[1] for x in sorted_value]

            ax.bar(x + i * width, p, width, label=key)
            i += 1
        ax.set_title('Пример групповой диаграммы')
        ax.set_xticks(x)
        ax.set_xticklabels(sizes)
        ax.legend()
        plt.show()

    @staticmethod
    def __build_path(result: BenchmarkWorkerResult):
        return '_'.join([result.test_code, str(result.size)])
"""


class ResultReader:
    def __init__(self, result_store: IResultStore, batch_size=100):
        self.result_store = result_store
        self.batch_size = batch_size
        self.offset = 0
        self.items: list[Any] = []
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.i += 1
        if self.i >= len(self.items):
            self.items = self.result_store.get_results(offset=self.offset, limit=self.batch_size)
            self.i = 0
            self.offset += self.batch_size
            if len(self.items) == 0:
                raise StopIteration
        return self.items[self.i]
