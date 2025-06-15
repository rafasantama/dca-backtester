"""Logging configuration for the DCA Backtester."""

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging with colored console output and optional file output.

    Args:
        debug: Whether to enable debug logging
        log_file: Optional path to log file
    """
    level = logging.DEBUG if debug else logging.INFO
    format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=Console(file=sys.stderr),
                show_time=True,
                show_path=True,
                rich_tracebacks=True,
            )
        ],
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        logging.getLogger().addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING) 