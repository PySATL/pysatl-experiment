from pathlib import Path

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.alternative.alternative import Alternative


class PowerReportBuilder:
    """
    Standard power report builder.
    """

    def __init__(
        self,
        criterion_config: CriterionConfig,
        sample_size: int,
        alternative: Alternative,
        significance_level: float,
        power_result: list[bool],
        results_path: Path,
    ):
        self.criterion_config = criterion_config
        self.sample_size = sample_size
        self.alternative = alternative
        self.significance_level = significance_level
        self.power_result = power_result
        self.results_path = results_path

    def build(self) -> None:
        """
        Build file from power report builder.
        """
        raise NotImplementedError("Method is not yet implemented")
