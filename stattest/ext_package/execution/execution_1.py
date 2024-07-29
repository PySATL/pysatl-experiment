import io

from stattest.test import AbstractTest, KSTest
import matplotlib.pyplot as plt
from fpdf import FPDF
import numpy as np

from stattest.test.generator import AbstractRVSGenerator, BetaRVSGenerator, CauchyRVSGenerator, LaplaceRVSGenerator, \
    LogisticRVSGenerator, TRVSGenerator, TukeyRVSGenerator
from stattest.test.normality import ADTest
from stattest.test.power import calculate_mean_test_power


class AbstractReportBlockGenerator:
    def build(self, pdf):
        raise NotImplementedError("Method is not implemented")

    @staticmethod
    def add_table(pdf, header, data, col_width=None, line_height=None, border=1, max_line_height=None):
        result = header + data

        if col_width is None:
            col_width = pdf.epw / 4

        if line_height is None:
            line_height = pdf.font_size * 2.5

        if max_line_height is None:
            max_line_height = pdf.font_size

        for row in result:
            for datum in row:
                pdf.multi_cell(col_width, line_height, datum, border=border, ln=3,
                               max_line_height=max_line_height)
            pdf.ln(line_height)

        return line_height * len(result)

    @staticmethod
    def add_image(pdf, image, h, w, x, y):
        pdf.image(image, h=h, w=w, x=x, y=y)


class PowerReportBlockGenerator(AbstractReportBlockGenerator):

    def __init__(self, tests: [AbstractTest], rvs_generators: [AbstractRVSGenerator], rvs_sizes=None, alpha=0.05,
                 count=1_000_000):
        self.tests = tests

        if rvs_sizes is None:
            rvs_sizes = [32, 64]

        self.rvs_sizes = rvs_sizes
        self.alpha = alpha
        self.count = count
        self.rvs_generators = rvs_generators
        self.rvs_sizes_str = [str(x) for x in rvs_sizes]
        self.header = [tuple(['Test'] + self.rvs_sizes_str)]

    def build(self, pdf):
        table_data = []

        for test in tests:
            result = self.calculate_multiple_test_power(test)
            powers = list(map(lambda x: str(x[1]), result))
            table_data.append(tuple([test.code()] + powers))

        return self.add_table(pdf, self.header, table_data)

    def calculate_multiple_test_power(self, test: AbstractTest):
        result = []

        for rvs_size in self.rvs_sizes:
            power = calculate_mean_test_power(test, rvs_generators=rvs_generators, rvs_size=rvs_size, alpha=self.alpha,
                                              count=self.count)
            result.append((rvs_size, power))

        return result


class PDFReportBlockGenerator(AbstractReportBlockGenerator):

    def __init__(self, tests: [AbstractTest], rvs_size, h=70, w=70, count=100_000):
        self.tests = tests
        self.rvs_size = rvs_size
        self.count = count
        self.h = h
        self.w = w

    def build(self, pdf):
        start_y = pdf.get_y()
        for test in self.tests:
            height = self.build_one(pdf, test, start_y)
            start_y = start_y + height

        return self.h * len(tests)

    def build_one(self, pdf, test, start_y):
        result = np.zeros(self.count)

        for i in range(self.count):
            x = test.generate_uniform(size=self.rvs_size)
            result[i] = test.execute_statistic(x)

        result.sort()

        fig, ax = plt.subplots()
        ax.set_title("PDF " + test.code())
        ax.hist(result, density=True, bins=100)
        ax.legend()

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        self.add_image(pdf, buf, h=self.h, w=self.w, x=20, y=start_y)

        return self.h


class ReportGenerator:

    def __init__(self, generators: [AbstractReportBlockGenerator], font='Times', padding=5):
        self.pdf = FPDF()
        self.pdf.set_font(font)
        self.pdf.add_page()
        self.generators = generators
        self.padding = padding

    def generate(self, path='report.pdf'):
        start_y = self.pdf.get_y()
        for generator in self.generators:
            height = generator.build(self.pdf)
            self.pdf.set_y(start_y + height + self.padding)

        self.pdf.output(path)


if __name__ == '__main__':
    tests = [KSTest(), ADTest()]
    rvs_generators = [BetaRVSGenerator(a=0.5, b=0.5)]  # , BetaRVSGenerator(a=1, b=1), BetaRVSGenerator(a=2, b=2),
    # CauchyRVSGenerator(t=0, s=0.5), CauchyRVSGenerator(t=0, s=1), CauchyRVSGenerator(t=0, s=2),
    # LaplaceRVSGenerator(t=0, s=1), LogisticRVSGenerator(t=2, s=2),
    # TRVSGenerator(df=1), TRVSGenerator(df=2), TRVSGenerator(df=4), TRVSGenerator(df=10),
    # TukeyRVSGenerator(lam=0.5), TukeyRVSGenerator(lam=2), TukeyRVSGenerator(lam=5),
    # TukeyRVSGenerator(lam=10)]
    sizes = [32]
    power_generator = PowerReportBlockGenerator(tests=tests, rvs_generators=rvs_generators, rvs_sizes=sizes)
    pdf_generator = PDFReportBlockGenerator(tests=tests, rvs_size=32)

    report_generator = ReportGenerator(generators=[power_generator, pdf_generator])
    report_generator.generate()
