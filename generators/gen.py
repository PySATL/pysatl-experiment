from stattest.core.distribution.beta import generate_beta
from stattest.experiment.generator import AbstractRVSGenerator


class BBBRVSGenerator(AbstractRVSGenerator):
    def __init__(self, a, b, **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.b = b

    def code(self):
        return super()._convert_to_code(['beta', self.a, self.b])

    def generate(self, size):
        return generate_beta(size=size, a=self.a, b=self.b)
