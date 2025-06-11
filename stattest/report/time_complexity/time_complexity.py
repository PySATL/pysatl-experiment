from pathlib import Path

from stattest.configuration.criteria_config.criteria_config import CriterionConfig


class TimeComplexityReportBuilder:
    """
    Standard time complexity report builder.
    """

    def __init__(
        self,
        criterion_config: CriterionConfig,
        sample_size: int,
        times: list[float],
        results_path: Path,
    ):
        self.criterion_config = criterion_config
        self.sample_size = sample_size
        self.times = times
        self.results_path = results_path

    def build(self) -> None:
        """
        Build file from time complexity report builder.
        """
        raise NotImplementedError("Method is not yet implemented")
