"""Generation step for labelled machine-learning samples."""

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any

import numpy as np
from line_profiler import profile
from pysatl_criterion import DistributionType
from pysatl_criterion.utils.generator import get_available_generator
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage
from pysatl_experiment.persistence.models.generated_samples import GeneratedSampleModel


@dataclass(frozen=True)
class GenerationOnlyStepData:
    """Inputs required to generate and persist labelled samples."""

    generation_run_id: int
    distribution: DistributionType
    sample_sizes: list[int]
    samples_count: int
    parameter_config: dict[str, dict[str, Any]]
    seed: int
    parallel_workers: int = 1


def _uint32_seed(sequence: np.random.SeedSequence) -> int:
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def _draw_parameters(parameter_config: dict[str, dict[str, Any]], rng: np.random.Generator) -> dict[str, float]:
    parameters = {}
    for name in sorted(parameter_config):
        rule = parameter_config[name]
        if rule["type"] == "fixed":
            parameters[name] = float(rule["value"])
        elif rule["type"] == "random_uniform":
            parameters[name] = float(rng.uniform(rule["low"], rule["high"]))
        else:
            raise ValueError(f"Unsupported parameter rule: {rule['type']}")
    return parameters


def _generate_sample(
    task: tuple[GenerationOnlyStepData, int, int],
) -> GeneratedSampleModel:
    step_data, sample_size, sample_num = task
    sequence = np.random.SeedSequence(
        [
            step_data.seed,
            len(step_data.distribution.value),
            *step_data.distribution.value.encode("utf-8"),
            sample_size,
            sample_num,
        ]
    )
    parameter_sequence, sample_sequence = sequence.spawn(2)
    parameter_seed = _uint32_seed(parameter_sequence)
    sample_seed = _uint32_seed(sample_sequence)
    parameters = _draw_parameters(step_data.parameter_config, np.random.default_rng(parameter_seed))
    generator = get_available_generator(step_data.distribution, parameters)
    data = generator.generate(sample_size, random_state=np.random.default_rng(sample_seed))
    sample = np.asarray(data, dtype=float)
    if sample.shape != (sample_size,):
        raise ValueError(
            f"Generator for {step_data.distribution.value} returned shape {sample.shape}, expected ({sample_size},)"
        )
    if not np.isfinite(sample).all():
        raise ValueError(f"Generator for {step_data.distribution.value} returned non-finite observations")
    return GeneratedSampleModel(
        generation_run_id=step_data.generation_run_id,
        sample_size=sample_size,
        sample_num=sample_num,
        parameters=parameters,
        sample_seed=sample_seed,
        data=sample.tolist(),
    )


class GenerationOnlyStep(IExperimentStep):
    """Draw distribution parameters per sample and persist samples immediately."""

    def __init__(self, step_data: GenerationOnlyStepData, storage: GeneratedSamplesStorage) -> None:
        self.step_data = step_data
        self.storage = storage

    @profile
    @override
    def run(self) -> None:
        """Generate and persist only missing sample numbers."""
        tasks = []
        for sample_size in self.step_data.sample_sizes:
            existing = self.storage.get_existing_sample_numbers(
                self.step_data.generation_run_id,
                sample_size,
            )
            for sample_num in range(1, self.step_data.samples_count + 1):
                if sample_num in existing:
                    continue
                tasks.append((self.step_data, sample_size, sample_num))

        if self.step_data.parallel_workers == 1:
            self._store_results(map(_generate_sample, tasks))
        elif tasks:
            chunksize = max(1, len(tasks) // (self.step_data.parallel_workers * 4))
            with ProcessPoolExecutor(max_workers=self.step_data.parallel_workers) as executor:
                self._store_results(executor.map(_generate_sample, tasks, chunksize=chunksize))

    def _store_results(self, results) -> None:
        batch = []
        for result in results:
            batch.append(result)
            if len(batch) == 100:
                self.storage.insert_samples(batch)
                batch = []
        self.storage.insert_samples(batch)
