"""
Configuration settings for the tokenify tool.
Refactored to allow easier testing of default compression logic.
"""
import gzip
import bz2
import lzma
from typing import Dict, Optional, Any
COMPRESSION_ALGORITHMS_DATA: Dict[str, Dict[str, Any]] = {
    "gzip": {"opener": getattr(gzip, "open", None), "extension": ".gz"},
    "bz2": {"opener": getattr(bz2, "open", None), "extension": ".bz2"},
    "lzma": {"opener": getattr(lzma, "open", None), "extension": ".xz"},
}
INITIAL_DEFAULT_COMPRESSION: str = "gzip"
def get_default_compression(
    algorithms: Optional[Dict] = None,
    initial_default: str = INITIAL_DEFAULT_COMPRESSION,
) -> str:
    """
    Determines the effective default compression algorithm based on availability.
    Args:
        algorithms (Optional[Dict]): Dictionary of available algorithms and their openers.
                                     Defaults to COMPRESSION_ALGORITHMS_DATA if None.
        initial_default (str): The preferred default algorithm ('gzip').
                                Defaults to INITIAL_DEFAULT_COMPRESSION.
    Returns:
        str: The name of the selected default compression algorithm.
    """
    if algorithms is None:
        algorithms = COMPRESSION_ALGORITHMS_DATA
    if (
        initial_default in algorithms
        and algorithms[initial_default].get("opener") is not None
    ):
        return initial_default
    for algo, settings in algorithms.items():
        if settings.get("opener") is not None:
            return algo
    return initial_default
DEFAULT_COMPRESSION: str = get_default_compression()
def is_compression_available(
    algo: Optional[str], algorithms: Optional[Dict] = None
) -> bool:
    """
    Checks if the required library/opener for a compression algorithm is available.
    Args:
        algo (Optional[str]): The name of the algorithm to check (e.g., 'gzip').
        algorithms (Optional[Dict]): Dictionary of available algorithms.
                                     Defaults to COMPRESSION_ALGORITHMS_DATA if None.
    Returns:
        bool: True if the algorithm is listed and its opener is available, False otherwise.
    """
    if algo is None:
        return False
    if algorithms is None:
        algorithms = COMPRESSION_ALGORITHMS_DATA
    return algo in algorithms and algorithms[algo].get("opener") is not None
def get_compression_settings(
    algo: Optional[str], algorithms: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the settings (opener, extension) for a given algorithm.
    Args:
        algo (Optional[str]): The name of the algorithm.
        algorithms (Optional[Dict]): Dictionary of available algorithms.
                                     Defaults to COMPRESSION_ALGORITHMS_DATA if None.
    Returns:
        Optional[Dict[str, Any]]: The settings dictionary or None if not found/invalid.
    """
    if algo is None:
        return None
    if algorithms is None:
        algorithms = COMPRESSION_ALGORITHMS_DATA
    return algorithms.get(algo)
COMPRESSION_ALGORITHMS = COMPRESSION_ALGORITHMS_DATA
