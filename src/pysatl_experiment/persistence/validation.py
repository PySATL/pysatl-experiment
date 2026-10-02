"""Validation shared by storage models and bulk operations."""


def require_nonempty_name(value: str, field: str) -> None:
    """Reject missing names without changing their identity."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")


def require_positive_integer(value: int, field: str) -> None:
    """Reject invalid sizes instead of silently coercing them."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
