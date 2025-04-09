import logging
from abc import ABC

import numpy as np
from fpdf import FPDF
from matplotlib import pyplot as plt

from stattest.experiment.configuration import ReportBuilder, TestWorkerResult
from stattest.experiment.test.worker import BenchmarkWorkerResult, PowerWorkerResult


logger = logging.getLogger(__name__)


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
        self.sizes = set()
        self.tests = set()
        self.font = "helvetica"
        self.border = 1
        self.align = "C"
        self.col_width = 30
        self.header_font_size = 12
        self.entry_font_size = 10
        self.output_filename = "power_report.pdf"

    def process(self, result: TestWorkerResult):
        if not isinstance(result, PowerWorkerResult):
            raise TypeError(f"Type {type(result)} is not an instance of PowerWorkerResult")

        key = PdfPowerReportBuilder.__build_path(result)
        self.sizes.add(result.size)
        self.tests.add(result.test_code)

        if key not in self.data:
            self.data[key] = {}

        if result.test_code not in self.data[key]:
            self.data[key][result.test_code] = {}

        self.data[key][result.test_code][result.size] = result.power

    def build(self):
        pdf = FPDF(orientation="L")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font(self.font, size=self.entry_font_size)

        sorted_sizes = sorted(self.sizes)
        sorted_tests = sorted(self.tests)
        table_width = (len(sorted_sizes) + 1) * self.col_width
        margin_x = (pdf.w - table_width) / 2

        for key, results in self.data.items():
            pdf.set_font(self.font, "B", self.header_font_size)
            pdf.cell(0, self.entry_font_size, f"{key}", ln=True, align="C")
            pdf.ln(5)

            pdf.set_x(margin_x)
            pdf.set_font(self.font, "B", self.entry_font_size)
            pdf.cell(
                self.col_width, self.entry_font_size, "Test", border=self.border, align=self.align
            )
            for size in sorted_sizes:
                pdf.cell(
                    self.col_width,
                    self.entry_font_size,
                    str(size),
                    border=self.border,
                    align=self.align,
                )
            pdf.ln()

            pdf.set_font(self.font, size=self.entry_font_size)
            for test in sorted_tests:
                test_name = test.split("_")[0]
                pdf.set_x(margin_x)
                pdf.cell(
                    self.col_width,
                    self.entry_font_size,
                    test_name,
                    border=self.border,
                    align=self.align,
                )
                for size in sorted_sizes:
                    power = results.get(test, {}).get(size, "N/A")
                    pdf.cell(
                        self.col_width,
                        self.entry_font_size,
                        f"{power:.3f}" if isinstance(power, float) else str(power),
                        border=self.border,
                        align=self.align,
                    )
                pdf.ln()
            pdf.ln(self.entry_font_size)

        pdf.output(self.output_filename)
        logger.info(f"PDF report saved as: {self.output_filename}")

    @staticmethod
    def __build_path(result: PowerWorkerResult):
        return f"Alternative: {result.alternative_code} alpha: {result.alpha}"


class ChartBenchmarkMeanReportBuilder(ReportBuilder):
    def __init__(self):
        self.data = {}
        self.sizes = set()
        self.codes = set()

    def process(self, result: BenchmarkWorkerResult):
        key = result.test_code  # ChartBenchmarkMeanReportBuilder.__build_path(result)
        point = (result.size, result.mean)
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
        ax.set_title("Пример групповой диаграммы")
        ax.set_xticks(x)
        ax.set_xticklabels(sizes)
        ax.legend()
        plt.show()

    @staticmethod
    def __build_path(result: BenchmarkWorkerResult):
        return "_".join([result.test_code, str(result.size)])
