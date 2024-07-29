class AbstractTest:  # TODO: rename to abstract criteria???
    @staticmethod
    def code():
        raise NotImplementedError("Method is not implemented")

    def test(self, rvs, alpha):
        raise NotImplementedError("Method is not implemented")

    def execute_statistic(self, rvs, **kwargs):
        raise NotImplementedError("Method is not implemented")

    def generate(self, size, **kwargs):
        raise NotImplementedError("Method is not implemented")

    def calculate_critical_value(self, rvs_size, alpha, count=500_000):
        raise NotImplementedError("Method is not implemented")
