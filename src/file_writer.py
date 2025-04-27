"""
Contains the FileWriter class responsible for writing processed data
to a file, stdout, potentially with compression. Adheres to SRP.
"""
import sys
import logging
from io import BytesIO
from pathlib import Path
from typing import (
    Optional,
    Dict,
    Any,
)
log = logging.getLogger(__name__)
# pylint: disable=too-few-public-methods
class FileWriter:
    """Handles writing data to a destination (file or stdout), with optional compression."""
    def __init__(
        self,
        compress: bool = False,
        compression_algo: Optional[str] = None,
        compression_settings: Optional[Dict[str, Any]] = None,
    ):
        """
        Initializes the FileWriter.
        Args:
            compress: Whether to compress the output.
            compression_algo: The name of the compression algorithm (e.g., 'gzip').
            compression_settings: Dictionary containing 'opener' and 'extension'.
        Raises:
            ValueError: If compression is requested but algo/settings are invalid/missing.
        """
        self.compress = compress
        self.compression_algo = compression_algo
        self.compression_settings = (
            compression_settings if isinstance(compression_settings, dict) else {}
        )
        if self.compress:
            if (
                not self.compression_algo
                or not self.compression_settings.get("opener")
                or not self.compression_settings.get("extension")
            ):
                error_msg = (
                    "Compression requested with algorithm '%s', but it is not "
                    "available or settings ('opener', 'extension') are missing/"
                    "invalid. Ensure library is installed and config is correct."
                )
                log.error(error_msg, self.compression_algo)
                raise ValueError(error_msg % self.compression_algo)
            log.debug(
                "FileWriter initialized for compression with algorithm: %s",
                self.compression_algo,
            )
        else:
            log.debug("FileWriter initialized without compression.")
    def write(self, data: bytes, target_path: Optional[Path]) -> None:
        """
        Writes data to the target path or stdout, handling compression extension.
        Args:
            data: The bytes data to write.
            target_path: The Path object for the output file (base path), or None for stdout.
        Raises:
            IOError: If writing fails.
            RuntimeError: If compression settings are inconsistent internally.
            Exception: For other unexpected errors.
        """
        effective_target_path = target_path
        if self.compress and target_path:
            expected_ext = str(self.compression_settings.get("extension", ""))
            if expected_ext and not str(target_path).endswith(expected_ext):
                effective_target_path = target_path.with_suffix(
                    target_path.suffix + expected_ext
                )
                log.debug(
                    "Adding compression extension: %s -> %s",
                    target_path,
                    effective_target_path,
                )
            else:
                log.debug(
                    "Target path %s already includes compression extension or no extension needed.",
                    target_path,
                )
        try:
            if self.compress:
                self._write_compressed(data, effective_target_path)
            else:
                self._write_uncompressed(data, effective_target_path)
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
    def _write_compressed(self, data: bytes, target_path: Optional[Path]) -> None:
        """Handles writing compressed data."""
        opener = self.compression_settings.get("opener")
        if not opener:
            raise RuntimeError(
                f"Compression opener for {self.compression_algo} is invalid."
            )
        mode = "wb"
        if target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            log.debug(
                "Writing compressed data to file: %s using %s",
                target_path,
                self.compression_algo,
            )
            with opener(target_path, mode) as f:  # type: ignore[operator]
                f.write(data)
        else:
            log.debug(
                "Writing compressed data to stdout using %s", self.compression_algo
            )
            buf = BytesIO()
            with opener(buf, mode) as f:  # type: ignore[operator]
                f.write(data)
            sys.stdout.buffer.write(buf.getvalue())
            log.debug("Finished writing compressed data to stdout.")
    def _write_uncompressed(self, data: bytes, target_path: Optional[Path]) -> None:
        """Handles writing uncompressed data."""
        if target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            log.debug("Writing uncompressed data to file: %s", target_path)
            with open(target_path, "wb") as f:
                f.write(data)
        else:
            log.debug("Writing uncompressed data to stdout")
            sys.stdout.buffer.write(data)
            log.debug("Finished writing uncompressed data to stdout.")
