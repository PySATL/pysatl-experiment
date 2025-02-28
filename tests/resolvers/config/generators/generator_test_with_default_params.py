from stattest.core.distribution.beta import generate_beta
from stattest.experiment.generator import AbstractRVSGenerator


class GeneratorTest(AbstractRVSGenerator):
    def __init__(self, a=1, b=2, **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.b = b

    def code(self):
        return super()._convert_to_code(["generator_test", self.a, self.b])

    def generate(self, size):
        return generate_beta(size=size, a=self.a, b=self.b)
