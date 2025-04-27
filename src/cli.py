# pylint: disable=too-many-return-statements,too-few-public-methods
"""
Contains the CLI class responsible for parsing command-line arguments
and orchestrating the tokenify process using other components.
"""
import argparse
import logging
import sys
import os
import tokenize
from pathlib import Path
from typing import List, Optional, Tuple, NamedTuple
from .path_resolver import PathResolver
from .file_writer import FileWriter
from .file_processor import FileProcessor
from .config import (
    COMPRESSION_ALGORITHMS,
    DEFAULT_COMPRESSION,
    is_compression_available,
    get_compression_settings,
)
log = logging.getLogger(__name__)
class OutputSettings(NamedTuple):
    """Holds settings related to output destination and format."""
    in_place: bool
    output_dir: Optional[Path]
    compress: bool
    algo: Optional[str]
    base_common_path: Path
class CLIRunner:
    """Helper class to manage the execution flow of the CLI."""
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.output_dir: Optional[Path] = None
        self.compression_algo: Optional[str] = None
        self.input_files: List[Path] = []
        self.base_common_path: Path = Path(os.getcwd())
        self.success_count = 0
        self.fail_count = 0
    def setup_and_validate(self) -> bool:
        """Sets up logging, validates arguments, and gathers files."""
        if not self.args:
            log.error("CLIRunner initialized with invalid arguments.")
            return False
        self._setup_logging()
        log.debug("Parsed arguments: %s", self.args)
        self.output_dir = self._validate_output_dir()
        if not self._validate_compression():
            return False
        if not self._gather_input_files():
            return False
        self._determine_base_path()
        return True
    def _setup_logging(self) -> None:
        """Configures logging level based on arguments."""
        log_level = logging.INFO
        if hasattr(self.args, "quiet") and self.args.quiet:
            log_level = logging.WARNING
        elif hasattr(self.args, "verbose") and self.args.verbose:
            log_level = logging.DEBUG
        root_logger = logging.getLogger()
        if not root_logger.hasHandlers():
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
            handler.setLevel(log_level)
        root_logger.setLevel(log_level)
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
        log.debug("Logging level set to: %s", logging.getLevelName(log_level))
    def _validate_output_dir(self) -> Optional[Path]:
        """Validates the output directory argument."""
        output_dir = self.args.output_dir
        if self.args.in_place and output_dir:
            log.warning(
                "--in-place option overrides --output-dir. "
                "Output directory will be ignored."
            )
            return None
        if output_dir:
            try:
                resolved_output_dir = output_dir.resolve()
                resolved_output_dir.mkdir(parents=True, exist_ok=True)
                log.info("Output directory set to: %s", resolved_output_dir)
                if not resolved_output_dir.is_dir():
                    log.error(
                        "Output path '%s' exists but is not a directory.",
                        resolved_output_dir,
                    )
                    sys.exit(1)
                return resolved_output_dir
            except PermissionError:
                log.error(
                    "Permission denied: Cannot create or access output "
                    "directory '%s'.",
                    output_dir,
                )
                sys.exit(1)
            except OSError as e:
                log.error(
                    "Could not create or access output directory '%s': %s",
                    output_dir,
                    e,
                )
                sys.exit(1)
        return None
    def _validate_compression(self) -> bool:
        """Validates compression arguments."""
        self.compression_algo = getattr(self.args, "algorithm", None)
        if self.args.compress and not self.compression_algo:
            log.error(
                "Compression requested (-z), but no compression libraries "
                "(gzip, bz2, lzma) are available or algorithm selected."
            )
            return False
        if self.args.compress and not is_compression_available(self.compression_algo):
            log.error(
                "Compression algorithm '%s' is not available. "
                "Ensure the library is installed.",
                self.compression_algo,
            )
            return False
        return True
    def _gather_input_files(self) -> bool:
        """Gathers and validates input files."""
        try:
            self.input_files = PathResolver.gather_python_files(self.args.paths)
        except Exception as e:
            log.error("Error gathering input files: %s", e, exc_info=True)
            return False
        if not self.input_files:
            log.error("No Python files found matching the specified paths.")
            return False
        log.info("Found %d Python file(s) to process.", len(self.input_files))
        return True
    def _determine_base_path(self) -> None:
        """Determines the common base path for calculating relative output paths."""
        if not self.input_files:
            self.base_common_path = Path(os.getcwd()).resolve()
            log.warning("No input files found, using CWD as base path.")
            return
        try:
            resolved_file_paths_str = [str(p.resolve()) for p in self.input_files]
            common_path_str = os.path.commonpath(resolved_file_paths_str)
            self.base_common_path = Path(common_path_str).resolve()
            if self.base_common_path.is_file():
                self.base_common_path = self.base_common_path.parent
        except ValueError:
            log.warning(
                "Could not determine a common base path for inputs (e.g., "
                "different drives or no commonality). Using parent of first file."
            )
            self.base_common_path = self.input_files[0].resolve().parent
        except Exception as e:
            log.warning("Error determining common base path: %s. Using CWD.", e)
            self.base_common_path = Path(os.getcwd()).resolve()
        log.debug("Using base path for relative output: %s", self.base_common_path)
    def _get_output_destination(
        self, file_path: Path, settings: OutputSettings
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """Calculates output paths based on settings."""
        base_output_path: Optional[Path] = None
        effective_output_path_for_log: Optional[Path] = None
        try:
            resolved_file_path = file_path.resolve()
        except OSError as e:
            log.warning(
                "Could not resolve input file path '%s': %s. Skipping.", file_path, e
            )
            return None, None
        algo_settings = get_compression_settings(settings.algo)
        if settings.in_place:
            if settings.compress:
                if not (algo_settings and algo_settings.get("extension")):
                    log.error(
                        "Invalid compression settings for in-place algo '%s'",
                        settings.algo,
                    )
                    return None, None
                ext = str(algo_settings["extension"])
                new_path = resolved_file_path.with_suffix(
                    resolved_file_path.suffix + ext
                )
                base_output_path = new_path
                effective_output_path_for_log = new_path
            else:
                base_output_path = resolved_file_path
                effective_output_path_for_log = resolved_file_path
        elif settings.output_dir:
            abs_output_dir = settings.output_dir
            abs_base_common_path = settings.base_common_path
            try:
                if not resolved_file_path.is_absolute():
                    resolved_file_path = resolved_file_path.resolve()
                relative_path = resolved_file_path.relative_to(abs_base_common_path)
            except ValueError:
                log.warning(
                    "File '%s' is outside base path '%s'. Using filename only.",
                    resolved_file_path,
                    abs_base_common_path,
                )
                relative_path = Path(resolved_file_path.name)
            except OSError as e:
                log.warning(
                    "Could not resolve path for relative calculation '%s': %s",
                    resolved_file_path,
                    e,
                )
                relative_path = Path(resolved_file_path.name)
            base_output_path = abs_output_dir / relative_path
            effective_output_path_for_log = base_output_path
            if settings.compress:
                if not (algo_settings and algo_settings.get("extension")):
                    log.error(
                        "Invalid compression settings for algo '%s'", settings.algo
                    )
                    return None, None
                ext = str(algo_settings["extension"])
                effective_output_path_for_log = base_output_path.with_suffix(
                    base_output_path.suffix + ext
                )
        log.debug(
            "Output destination for %s: base=%s, log_path=%s",
            resolved_file_path,
            base_output_path,
            effective_output_path_for_log,
        )
        return base_output_path, effective_output_path_for_log
    def _remove_original_if_compressed_inplace(
        self, original_path: Path, compressed_path: Path
    ) -> None:
        """Removes the original file after successful in-place compression."""
        try:
            resolved_original = original_path.resolve()
            resolved_compressed = compressed_path.resolve()
            if resolved_original.exists() and resolved_original != resolved_compressed:
                os.unlink(resolved_original)
                log.debug(
                    "Removed original file after in-place compression: %s",
                    resolved_original,
                )
            elif resolved_original == resolved_compressed:
                log.debug(
                    "Original file path same as compressed, not removing: %s",
                    resolved_original,
                )
            elif not resolved_original.exists():
                log.debug(
                    "Original file %s does not exist, skipping removal.",
                    resolved_original,
                )
        except OSError as e:
            log.warning(
                "Could not remove original file %s after in-place compression: %s",
                original_path,
                e,
            )
        except Exception as e:
            log.warning(
                "Error during post-compression cleanup for %s: %s", original_path, e
            )
    def _process_single_file(self, file_path: Path) -> bool:
        """Processes a single input file."""
        output_settings = OutputSettings(
            in_place=self.args.in_place,
            output_dir=self.output_dir,
            compress=self.args.compress,
            algo=self.compression_algo,
            base_common_path=self.base_common_path,
        )
        output_dest, effective_log_path = self._get_output_destination(
            file_path, output_settings
        )
        if (
            output_dest is None
            and effective_log_path is None
            and not (output_settings.in_place or output_settings.output_dir is None)
        ):
            log.warning(
                "Could not determine output destination for %s, skipping.", file_path
            )
            return False
        try:
            comp_settings = get_compression_settings(self.compression_algo)
            writer = FileWriter(
                compress=self.args.compress,
                compression_algo=self.compression_algo,
                compression_settings=comp_settings,
            )
            processor = FileProcessor(input_path=file_path, writer=writer)
            processor.process(output_dest)
            if effective_log_path:
                action = (
                    "[Modified]"
                    if self.args.in_place and not self.args.compress
                    else "[Compressed]" if self.args.compress else "[Written]"
                )
                log.info("%s %s", action, effective_log_path)
            if self.args.in_place and self.args.compress and effective_log_path:
                self._remove_original_if_compressed_inplace(
                    file_path, effective_log_path
                )
            return True
        except (ValueError, TypeError) as e:
            log.error("Configuration or processing error for %s: %s", file_path, e)
            return False
        except FileNotFoundError:
            log.error("File not found error for %s.", file_path)
            return False
        except PermissionError:
            log.error("Permission error processing %s.", file_path)
            return False
        except tokenize.TokenError:
            log.error("Tokenization error for %s.", file_path)
            return False
        except IOError:
            log.error("IO error processing %s.", file_path)
            return False
        except Exception as e:
            log.error(
                "Failed to process %s. Error: %s",
                file_path,
                e,
                exc_info=log.level <= logging.DEBUG,
            )
            return False
    def run(self) -> int:
        """Executes the main processing loop."""
        if not self.setup_and_validate():
            return 1
        for file_path in self.input_files:
            if self._process_single_file(file_path):
                self.success_count += 1
            else:
                self.fail_count += 1
        log.info(
            "Processing complete. %d file(s) succeeded, %d file(s) failed.",
            self.success_count,
            self.fail_count,
        )
        return 1 if self.fail_count > 0 else 0
class CLI:
    """Command Line Interface handler."""
    def __init__(self):
        self.parser = self._create_parser()
    def _create_parser(self) -> argparse.ArgumentParser:
        """Creates the argument parser."""
        available_algos = [
            algo for algo in COMPRESSION_ALGORITHMS if is_compression_available(algo)
        ]
        epilog_text = """Examples (when run as script):
  tokenify script.py
  tokenify -i project_dir
Examples (when run as module):
  python -m src.main script.py
  python -m src.main -i project_dir
  python -m src.main -o cleaned_dir script1.py script2.py
  python -m src.main "src/**/*.py"
  python -m src.main -o cleaned_dir -z -a lzma project_dir"""
        parser = argparse.ArgumentParser(
            prog="tokenify",
            description="Strip comments and optionally compress Python files.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            exit_on_error=False,
            epilog=epilog_text,
        )
        parser.add_argument(
            "paths",
            nargs="+",
            help="File, directory, or glob pattern paths to process.",
        )
        parser.add_argument(
            "-i",
            "--in-place",
            action="store_true",
            help="Modify files in place. Overrides --output-dir.",
        )
        parser.add_argument(
            "-o",
            "--output-dir",
            type=Path,
            help="Directory to save processed files. Ignored if --in-place.",
        )
        parser.add_argument(
            "-z",
            "--compress",
            action="store_true",
            help="Compress output files. Requires relevant library (e.g., gzip).",
        )
        if available_algos:
            current_default = (
                DEFAULT_COMPRESSION
                if DEFAULT_COMPRESSION in available_algos
                else (available_algos[0] if available_algos else None)
            )
            default_help = f" (default: {current_default})" if current_default else ""
            parser.add_argument(
                "-a",
                "--algorithm",
                choices=available_algos,
                default=current_default,
                help=f"Compression algorithm{default_help}. "
                "Requires corresponding library.",
            )
        else:
            parser.add_argument("-a", "--algorithm", help=argparse.SUPPRESS)
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Suppress info messages (show warnings/errors).",
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Show debug messages."
        )
        return parser
    def run(self, args: Optional[List[str]] = None) -> None:
        """Parses arguments and orchestrates the file processing."""
        parsed_args: Optional[argparse.Namespace] = None
        try:
            parsed_args = self.parser.parse_args(args)
        except argparse.ArgumentError as e:
            log.error("Argument error: %s", e)
            stderr = getattr(sys, "stderr", None)
            if stderr:
                try:
                    self.parser.print_usage(stderr)
                except Exception:  # pylint: disable=broad-except
                    log.debug("Could not print usage to stderr.")
            sys.exit(2)
        runner = CLIRunner(parsed_args)
        exit_code = runner.run()
        sys.exit(exit_code)
