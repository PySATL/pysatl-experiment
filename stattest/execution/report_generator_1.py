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
