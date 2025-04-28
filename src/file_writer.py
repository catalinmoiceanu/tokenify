"""
Contains the FileWriter class responsible for writing processed data
to a file or stdout. Compression logic has been removed. Adheres to SRP.
"""
import sys
import logging
from pathlib import Path
from typing import Optional
log = logging.getLogger(__name__)
# pylint: disable=too-few-public-methods
class FileWriter:
    """Handles writing data to a destination (file or stdout)."""
    def __init__(self):
        """
        Initializes the FileWriter. Compression parameters removed.
        """
        log.debug("FileWriter initialized.")
    def write(self, data: bytes, target_path: Optional[Path]) -> None:
        """
        Writes data to the target path or stdout.
        Args:
            data: The bytes data to write.
            target_path: The Path object for the output file, or None for stdout.
        Raises:
            IOError: If writing fails.
            Exception: For other unexpected errors.
        """
        effective_target_path = target_path
        try:
            if target_path:
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    log.error("Could not create directory for %s: %s", target_path, e)
                    raise IOError(f"Could not create directory for {target_path}: {e}") from e
                log.debug("Writing data to file: %s", target_path)
                try:
                    with open(target_path, "wb") as f:
                        f.write(data)
                except OSError as e:
                    log.error("Could not write to file %s: %s", target_path, e)
                    raise IOError(f"Could not write to file {target_path}: {e}") from e
            else:
                log.debug("Writing data to stdout")
                try:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                except OSError as e:
                    log.error("Could not write to stdout: %s", e)
                    raise IOError(f"Could not write to stdout: {e}") from e
                log.debug("Finished writing data to stdout.")
        except IOError as e:
            log.error("IOError writing to %s: %s", effective_target_path or "stdout", e)
            raise
        except Exception as e:
            log.error(
                "Unexpected error during write to %s: %s",
                effective_target_path or "stdout",
                e,
                exc_info=True,
            )
            raise
