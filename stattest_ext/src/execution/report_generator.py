import math
from collections import Counter

import numpy as np
from fpdf import FPDF

from stattest_ext.src.execution.cache import CacheResultService


class AbstractReportBlockGenerator:
    def build(self, pdf):
        raise NotImplementedError("Method is not implemented")


class ImageReportBlockGenerator(AbstractReportBlockGenerator):
    def build(self, pdf):
        raise NotImplementedError("Method is not implemented")

    @staticmethod
    def add_image(pdf, image, h, w, x, y):
        pdf.image(image, h=h, w=w, x=x, y=y)


class TableReportBlockGenerator(AbstractReportBlockGenerator):
    def build(self, pdf):
        raise NotImplementedError("Method is not implemented")

    @staticmethod
    def add_table(pdf, header: [tuple], data: [tuple], col_width=None, line_height=None, border=1,
                  max_line_height=None):
        result = [[str(x) for x in tup] for tup in header] + [[str(x) for x in tup] for tup in data]

        if col_width is None:
            col_width = pdf.epw / len(header[0])

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


class ReportGenerator:

    def __init__(self, generators: [AbstractReportBlockGenerator], font='Times', padding=5):
        self.pdf = FPDF(orientation='L')
        self.pdf.set_font(font)
        self.pdf.add_page()
        self.generators = generators
        self.padding = padding

    def generate(self, path='report.pdf'):
        start_y = self.pdf.get_y()
        for generator in self.generators:
            height = generator.build(self.pdf)
            start_y = start_y + height + self.padding
            self.pdf.set_y(start_y)

        self.pdf.output(path)


class PowerTableReportBlockGenerator(TableReportBlockGenerator):
    def __init__(self, data_path='result/result.json'):
        self.cache = CacheResultService(filename=data_path, separator=':')

    def build_table_alternative(self, pdf, alternative):
        significant_levels = self.cache.get_level_prefixes([alternative], 1)
        height = 0
        for significant_level in significant_levels:
            height = height + self.build_table(pdf, alternative, significant_level)

        return height

    def build_table(self, pdf, alternative, significant_level):
        pdf.text(y=pdf.get_y() + 10, x=10,
                 text='Alternative: ' + alternative + ' Significant level: ' + significant_level)
        pdf.set_y(pdf.get_y() + 15)

        values = self.cache.get_with_prefix([alternative, significant_level])

        test_codes_all = set()
        sizes = set()
        for key in values:
            split = key.split(':')
            test_codes_all.add(split[-1])
            sizes.add(int(split[-2]))

        test_codes_all = list(test_codes_all)
        sizes = list(sizes)
        sizes.sort()
        data = [[0] * (len(sizes) + 1) for i in range(len(test_codes_all))]
        for i in range(len(test_codes_all)):
            data[i][0] = test_codes_all[i]
        for key in values:
            split = key.split(':')
            index_test = test_codes_all.index(split[-1])
            index_size = sizes.index(int(split[-2]))
            data[index_test][index_size + 1] = round(values[key], 2)

        return self.add_table(pdf, [['Test'] + sizes], data) + 10

    def build(self, pdf):
        alternatives = self.cache.get_level_prefixes([], 0)
        height = 0
        for alternative in alternatives:
            height = height + self.build_table_alternative(pdf, alternative)

        return height


class TopPowerTableReportBlockGenerator(TableReportBlockGenerator):
    def __init__(self, data_path='result/result.json'):
        self.cache = CacheResultService(filename=data_path, separator=':')

    def build_table_alternative(self, pdf, alternative, data, index_alternative):
        significant_levels = self.cache.get_level_prefixes([alternative], 1)
        height = 0
        for significant_level in significant_levels:
            height = height + self.build_table(pdf, alternative, significant_level, data, index_alternative)

        return height

    def build_table(self, pdf, alternative, significant_level, result, index_alternative):
        values = self.cache.get_with_prefix([alternative, significant_level])

        test_codes_all = set()
        sizes = set()
        for key in values:
            split = key.split(':')
            test_codes_all.add(split[-1])
            sizes.add(int(split[-2]))

        test_codes_all = list(test_codes_all)
        sizes = list(sizes)
        sizes.sort()
        data = [[0] * (len(sizes) + 1) for i in range(len(test_codes_all))]
        for i in range(len(test_codes_all)):
            data[i][0] = test_codes_all[i]
        for key in values:
            split = key.split(':')
            index_test = test_codes_all.index(split[-1])
            index_size = sizes.index(int(split[-2]))
            data[index_test][index_size + 1] = round(values[key], 5)

        s1 = set()
        s2 = set()
        s3 = set()
        for i in range(len(sizes)):
            ind = np.argpartition(data[:][i], -2)[-2:]
            s = [data[i][0] for i in ind]
            if int(sizes[i]) < 100:
                for j in range(len(s)):
                    s1.add(s[j])
            elif int(sizes[i]) < 500:
                for j in range(len(s)):
                    s2.add(s[j])
            else:
                for j in range(len(s)):
                    s3.add(s[j])

        if float(significant_level) == 0.1:
            shift = 0
        elif float(significant_level) == 0.05:
            shift = 1
        else:
            shift = 2

        result[index_alternative][1 + shift] = ','.join(s1)
        result[index_alternative][4 + shift] = ','.join(s2)
        result[index_alternative][7 + shift] = ','.join(s3)

        return 10

    def build(self, pdf):
        alternatives = list(self.cache.get_level_prefixes([], 0))
        height = 0
        headers = ['Alternative', '<100 0.1', '<100 0.05', '<100 0.01', '100-499 0.1', '100-499 0.05', '100-499 0.01',
                   '>=500 0.1', '>=500 0.05', '>=500 0.01']
        data = [[0] * len(headers) for i in range(len(alternatives))]
        for i in range(len(alternatives)):
            data[i][0] = alternatives[i]
        for alternative in alternatives:
            index_alternative = alternatives.index(alternative)
            height = height + self.build_table_alternative(pdf, alternative, data, index_alternative)

        return self.add_table(pdf, [headers], data, line_height=pdf.font_size * 6.5) + 10


class TopTestTableReportBlockGenerator(TableReportBlockGenerator):
    def __init__(self, data_path='result/result.json', hypothesis=None):
        if hypothesis is None:
            hypothesis = []
        self.cache = CacheResultService(filename=data_path, separator=':')
        self.hypothesis = hypothesis

    def build_table_alternative(self, pdf, alternative, test1, test2, test3):
        significant_levels = self.cache.get_level_prefixes([alternative], 1)
        height = 0
        for significant_level in significant_levels:
            height = height + self.build_table(pdf, alternative, significant_level, test1, test2, test3)

        return height

    def build_table(self, pdf, alternative, significant_level, test1, test2, test3):
        if float(significant_level) != 0.05:
            return 0
        if len(self.hypothesis) > 0 and not alternative in self.hypothesis:
            return 0

        values = self.cache.get_with_prefix([alternative, significant_level])

        test_codes_all = set()
        sizes = set()
        for key in values:
            split = key.split(':')
            test_codes_all.add(split[-1])
            sizes.add(int(split[-2]))

        test_codes_all = list(test_codes_all)
        sizes = list(sizes)
        sizes.sort()
        data = [[0] * (len(sizes) + 1) for i in range(len(test_codes_all))]
        for i in range(len(test_codes_all)):
            data[i][0] = test_codes_all[i]
        for key in values:
            split = key.split(':')
            index_test = test_codes_all.index(split[-1])
            index_size = sizes.index(int(split[-2]))
            data[index_test][index_size + 1] = round(values[key], 5)

        s1 = set()
        s2 = set()
        s3 = set()
        maximum_count = 5
        for i in range(1, len(sizes)):
            tmp = [data[j][i] for j in range(len(test_codes_all))]
            ind = np.argpartition(tmp, -maximum_count)[-maximum_count:]
            s = [] #[data[j][0] for j in ind]
            for j in ind:
                for l in range(len(tmp)):
                    if tmp[l] == tmp[j]:
                        s.append(data[l][0])
            if int(sizes[i]) < 100:
                for j in range(len(s)):
                    s1.add(s[j])
            elif int(sizes[i]) < 500:
                for j in range(len(s)):
                    s2.add(s[j])
            else:
                for j in range(len(s)):
                    s3.add(s[j])

        test1.extend(s1)
        test2.extend(s2)
        test3.extend(s3)

        return 10

    def build(self, pdf):
        alternatives = list(self.cache.get_level_prefixes([], 0))
        height = 0
        headers = ['Test', '<100', '100-499', '>=500']
        test1 = []
        test2 = []
        test3 = []
        for alternative in alternatives:
            height = height + self.build_table_alternative(pdf, alternative, test1, test2, test3)

        all_tests = list(set(test1 + test2 + test3))
        data = [[0] * len(headers) for i in range(len(all_tests))]
        for i in range(len(all_tests)):
            data[i][0] = all_tests[i]

        counter1 = Counter(test1)
        counter2 = Counter(test2)
        counter3 = Counter(test3)

        for i in range(len(all_tests)):
            data[i][1] = counter1.get(all_tests[i], 0)
            data[i][2] = counter2.get(all_tests[i], 0)
            data[i][3] = counter3.get(all_tests[i], 0)

        return self.add_table(pdf, [headers], data) + 10


class PowerTableReportTimeBlockGenerator(TableReportBlockGenerator):
    def __init__(self, data_path='times.json'):
        self.cache = CacheResultService(filename=data_path, separator=':')

    def build(self, pdf):
        values = self.cache.get_with_prefix([])

        test_codes_all = set()
        sizes = set()
        for key in values:
            split = key.split(':')
            test_codes_all.add(split[1])
            sizes.add(int(split[0]))

        test_codes_all = list(test_codes_all)
        sizes = list(sizes)
        sizes.sort()
        data = [[0] * (len(sizes) + 1) for i in range(len(test_codes_all))]
        for i in range(len(test_codes_all)):
            data[i][0] = test_codes_all[i]
        for test in test_codes_all:
            for size in sizes:
                index_test = test_codes_all.index(test)
                index_size = sizes.index(size)
                mean = self.cache.get_with_level([str(size), test, 'mean'])
                std = self.cache.get_with_level([str(size), test, 'std'])
                median = self.cache.get_with_level([str(size), test, 'median'])
                per = self.cache.get_with_level([str(size), test, 'per'])
                data[index_test][index_size + 1] = ', '.join(
                    [str(round(mean, 4)), str(round(std, 4)), str(round(median, 4)), str(round(per, 4))])

        return self.add_table(pdf, [['Test'] + sizes], data, line_height=pdf.font_size * 6.5) + 10


"""
if __name__ == '__main__':
    report_generator = ReportGenerator([PowerTableReportTimeBlockGenerator()])
    report_generator.generate()
"""
