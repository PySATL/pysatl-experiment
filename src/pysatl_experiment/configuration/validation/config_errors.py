"""Configuration errors independent of CLI presentation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigIssue:
    """One invalid value identified by its location in the JSON document."""

    path: tuple[str | int, ...]
    code: str
    message: str

    def __str__(self) -> str:
        """Format a readable field path while retaining structured metadata."""
        path = ""
        for part in self.path:
            path += f"[{part}]" if isinstance(part, int) else ("." if path else "") + part
        return f"{path or '$'}: {self.message}"


class ConfigValidationError(ValueError):
    """Collect all configuration issues found in one validation pass."""

    def __init__(self, issues: list[ConfigIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("\n".join(map(str, issues)))


class ConfigReadError(ValueError):
    """Report a file read or JSON syntax error before domain validation."""
