"""
Contains the FileProcessor class, responsible for orchestrating the
processing of a single file (reading, stripping, writing). Adheres to SRP
and uses dependency injection for the writer.
"""
import logging
import tokenize
from pathlib import Path
from .comment_stripper import CommentStripper
from .file_writer import FileWriter
log = logging.getLogger(__name__)
# pylint: disable=too-few-public-methods
class FileProcessor:
    """Handles processing (reading, stripping, writing) of a single file."""
    def __init__(self, input_path: Path, writer: FileWriter):
        """
        Initializes the FileProcessor.
        Args:
            input_path: Path to the input Python file.
            writer: An instance of FileWriter to handle output.
        """
        if not isinstance(input_path, Path):
            raise TypeError("input_path must be a Path object")
        if not isinstance(writer, FileWriter):
            raise TypeError("writer must be a FileWriter instance")
        self.input_path = input_path
        self.writer = writer
        log.debug("FileProcessor initialized for input: %s", self.input_path)
    def process(self, output_path: Path | None) -> None:
        """
        Reads the file, strips comments, and uses the writer to output the result.
        Args:
            output_path: The target path for the output (can be None for stdout).
        Returns:
            None. Exceptions are raised on failure.
        Raises:
            FileNotFoundError: If the input file cannot be found.
            PermissionError: If there are permission issues reading or writing.
            tokenize.TokenError: If the file content cannot be tokenized.
            IOError: If writing fails (propagated from FileWriter).
            Exception: For other unexpected errors.
        """
        log.info("Processing file: %s", self.input_path)
        try:
            log.debug("Reading file content from: %s", self.input_path)
            source_bytes = self._read_file()
            log.debug("Stripping comments...")
            cleaned_bytes = CommentStripper.strip(source_bytes)
            log.debug(
                "Writing output via FileWriter to target: %s", output_path or "stdout"
            )
            self.writer.write(cleaned_bytes, output_path)
            log.debug("Successfully processed and wrote file: %s", self.input_path)
        except FileNotFoundError:
            log.error("Input file not found: %s", self.input_path)
            raise
        except PermissionError as e:
            log.error(
                "Permission denied reading %s or writing to target %s: %s",
                self.input_path,
                output_path,
                e,
            )
            raise
        except tokenize.TokenError:
            log.error("Skipping file due to tokenization error: %s", self.input_path)
            raise
        except IOError:
            log.error(
                "Skipping file due to write error for target: %s",
                output_path or "stdout",
            )
            raise
        except Exception as e:
            log.error(
                "Unexpected error processing %s: %s",
                self.input_path,
                e,
                exc_info=True,
            )
            raise
    def _read_file(self) -> bytes:
        """Reads the content of the input file."""
        try:
            with open(self.input_path, "rb") as f:
                content = f.read()
            log.debug("Read %d bytes from %s", len(content), self.input_path)
            return content
        except FileNotFoundError:
            log.error("Failed to read file %s: File not found.", self.input_path)
            raise
        except PermissionError as e:
            log.error(
                "Failed to read file %s: Permission denied. %s", self.input_path, e
            )
            raise
        except OSError as e:
            log.error("Failed to read file %s: %s", self.input_path, e)
            raise
