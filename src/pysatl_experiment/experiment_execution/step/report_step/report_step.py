"""Load results and invoke an injected report builder for any experiment."""

from collections.abc import Iterable
from pathlib import Path
from typing import Generic, TypeVar

from line_profiler import profile
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment_execution.step.report_step.abstract_report_builder import IReportBuilder
from pysatl_experiment.experiment_execution.step.report_step.report_context import (
    ReportBuilderContext,
    ReportStepContext,
)


ResultT = TypeVar("ResultT")


class ReportBuildingStep(IExperimentStep, Generic[ResultT]):
    """Read all selected results before allowing the builder to create files.

    The source owns selection and completeness checks. Reusable sources must
    return a fresh iterator for each run; a supplied iterator is single-use.
    """

    def __init__(
        self,
        context: ReportStepContext,
        result_storage: Iterable[ResultT],
        report_builder: IReportBuilder[ReportBuilderContext[ResultT]],
    ) -> None:
        self.context = context
        self.result_storage = result_storage
        self.report_builder = report_builder

    @property
    def results_path(self) -> Path:
        """Return the configured output directory."""
        return self.context.results_path

    @profile
    @override
    def run(self) -> None:
        """Materialize results and pass them with output settings to the builder."""
        data = tuple(self.result_storage)
        self.report_builder.build(
            ReportBuilderContext(
                report_name=self.context.report_name,
                report_mode=self.context.report_mode,
                results_path=self.context.results_path,
                template_path=self.context.template_path,
                data=data,
            )
        )
