"""Custom exceptions for the DCA Backtester."""

from typing import Optional


class DCAError(Exception):
    """Base exception for all DCA Backtester errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize the exception with a message and optional details.

        Args:
            message: The main error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(f"{message}{f' - {details}' if details else ''}")


class ClientError(DCAError):
    """Raised when there's an error with external API clients."""


class SimulationError(DCAError):
    """Raised when there's an error during simulation."""


class ConfigurationError(DCAError):
    """Raised when there's an error in configuration settings."""


class BacktestError(Exception):
    """Base exception for backtesting errors."""
    pass 