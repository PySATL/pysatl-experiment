from matplotlib import pyplot as plt

from stattest.experiment.configuration import ReportBuilder, TestWorkerResult
from stattest.experiment.test.worker import PowerWorkerResult


class ChartPowerReportBuilder(ReportBuilder):
    def __init__(self):
        self.data = {}

    def process(self, result: TestWorkerResult):
        if not isinstance(result, PowerWorkerResult):
            raise TypeError(f"Type {type(result)} is not instance of PowerWorkerResult")

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

            ax.set(
                xlabel="time (s)",
                ylabel="voltage (mV)",
                title="About as simple as it gets, folks",
            )
            ax.grid()

            fig.savefig("test.png")
            plt.show()

    @staticmethod
    def __build_path(result: PowerWorkerResult):
        return "_".join([result.test_code, str(result.alternative_code), str(result.alpha)])


class PdfPowerReportBuilder(ReportBuilder):
    def __init__(self):
        self.data = {}

    def process(self, result: TestWorkerResult):
        pass

    def build(self):
        pass
