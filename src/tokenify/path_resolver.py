"""
Contains the PathResolver class responsible for finding Python files
based on input paths (files, directories, globs). Adheres to SRP.
"""
import glob
import logging
from pathlib import Path
from typing import List, Set
log = logging.getLogger(__name__)
# pylint: disable=too-few-public-methods
class PathResolver:
    """Resolves input paths (files, directories, globs) into a list of Python files."""
    @staticmethod
    def _process_single_target(target_str: str, python_files: Set[Path]) -> None:
        """Processes a single resolved target path (file or directory)."""
        try:
            target_path = Path(target_str).resolve()
            log.debug("Checking resolved path: %s", target_path)
            if not target_path.exists():
                log.warning(
                    "Path does not exist: %s (from input '%s')", target_path, target_str
                )
                return
            if target_path.is_dir():
                log.debug("Path is a directory, searching recursively: %s", target_path)
                count = 0
                for item in target_path.rglob("*.py"):
                    if item.is_file():
                        log.debug("Found Python file: %s", item)
                        python_files.add(item)
                        count += 1
                log.debug("Found %d Python files in directory: %s", count, target_path)
            elif target_path.is_file():
                log.debug("Path is a file: %s", target_path)
                if target_path.suffix == ".py":
                    log.debug("Adding Python file: %s", target_path)
                    python_files.add(target_path)
                else:
                    log.warning("Skipping non-Python file: %s", target_path)
            else:
                log.warning("Skipping non-file/non-directory path: %s", target_path)
        except OSError as e:
            log.warning("Error resolving or accessing path '%s': %s", target_str, e)
        except (
            Exception
        ) as e:
            log.error(
                "Unexpected error processing path '%s': %s",
                target_str,
                e,
                exc_info=True,
            )
    @staticmethod
    def gather_python_files(paths: List[str]) -> List[Path]:
        """
        Finds all unique .py files from the given paths.
        Args:
            paths: A list of strings representing file paths, directory paths, or glob patterns.
        Returns:
            A sorted list of unique Path objects pointing to Python files.
        """
        python_files: Set[Path] = set()
        log.debug("Gathering Python files from input paths: %s", paths)
        for path_str in paths:
            log.debug("Processing input path string: '%s'", path_str)
            try:
                glob_matches = glob.glob(path_str, recursive=True)
                log.debug("Glob matches for '%s': %s", path_str, glob_matches)
            except Exception as e:
                log.warning("Could not process glob pattern '%s': %s", path_str, e)
                continue
            targets_to_check = glob_matches if glob_matches else [path_str]
            log.debug("Targets to check for '%s': %s", path_str, targets_to_check)
            for target_str in targets_to_check:
                PathResolver._process_single_target(target_str, python_files)
        sorted_files = sorted(list(python_files))
        log.debug("Total unique Python files found: %d", len(sorted_files))
        return sorted_files
