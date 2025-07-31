import timeit

from pysatl_experiment.experiment.configuration.configuration import StepListener


class TimeEstimationListener(StepListener):
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def before(self) -> None:
        self.start_time = timeit.default_timer()

    def after(self) -> None:
        self.end_time = timeit.default_timer()
        print("Generation time (s)", self.end_time - self.start_time)
