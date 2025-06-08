from pathlib import Path

from stattest.configuration.criteria_config.criteria_config import CriterionConfig


class CriticalValueReportBuilder:
    """
    Standard critical value report builder.
    """

    def __init__(
        self,
        criterion_config: CriterionConfig,
        sample_size: int,
        significance_level: float,
        limit_distribution: list[float],
        results_path: Path,
    ):
        self.criterion_config = criterion_config
        self.sample_size = sample_size
        self.significance_level = significance_level
        self.limit_distribution = limit_distribution
        self.results_path = results_path

    def build(self) -> None:
        """
        Build file from critical value report builder.
        """
        raise NotImplementedError("Method is not yet implemented")
