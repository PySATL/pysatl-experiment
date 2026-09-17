"""Utility for normalizing experiment names."""


def normalize_experiment_name(name: str) -> str:
    """Normalize an experiment name for filesystem usage."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")
