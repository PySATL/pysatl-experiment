import multiprocessing as mp

from click import ClickException, Context, IntRange, argument, echo, pass_context

from pysatl_experiment.cli.commands.common.common import get_experiment_name_and_config, save_experiment_config
from pysatl_experiment.cli.commands.configure.configure import configure


@configure.command()
@argument("workers", type=IntRange(min=1))
@pass_context
def parallel_workers(ctx: Context, workers: int) -> None:
    """
    Configure number of parallel workers for execution step.

    :param ctx: Click context.
    :param workers: Number of parallel workers (1 <= workers).
    """

    experiment_name, experiment_config = get_experiment_name_and_config(ctx)

    max_possible = mp.cpu_count()
    if workers > max_possible:
        raise ClickException(
            f"Cannot set parallel workers to {workers}. "
            f"Your machine has only {max_possible} CPU cores. "
            f"Please specify a value between 1 and {max_possible}."
        )

    experiment_config["parallel_workers"] = workers
    save_experiment_config(ctx, experiment_name, experiment_config)

    echo(f"Parallel workers for experiment '{experiment_name}' are set to {workers}.")
