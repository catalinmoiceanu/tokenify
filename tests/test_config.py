# pylint: disable=missing-module-docstring, missing-class-docstring
import unittest
from unittest.mock import MagicMock

# Import the refactored functions and constants from the config module
from src.config import (
    is_compression_available,
    get_default_compression,
)


class TestConfig(unittest.TestCase):

    # --- Tests for is_compression_available ---

    def test_is_compression_available_real_gzip(self):
        """Test with real modules (assuming gzip is standard)."""
        self.assertTrue(is_compression_available("gzip"))

    def test_is_compression_available_mocked_false(self):
        """Test with a mocked dict where the algorithm opener is None."""
        mock_algos = {"testzip": {"opener": None, "extension": ".tz"}}
        self.assertFalse(is_compression_available("testzip", algorithms=mock_algos))

    def test_is_compression_available_mocked_non_existent(self):
        """Test with a mocked dict that doesn't contain the algorithm."""
        mock_algos = {"gzip": {"opener": MagicMock(), "extension": ".gz"}}
        self.assertFalse(
            is_compression_available("nonexistentzip", algorithms=mock_algos)
        )

    # --- Tests for get_default_compression logic ---

    def test_get_default_compression_initial_available(self):
        """Test when the initial default ('gzip') is available."""
        mock_algos = {
            "gzip": {"opener": MagicMock(), "extension": ".gz"},
            "bz2": {"opener": MagicMock(), "extension": ".bz2"},
            "lzma": {"opener": MagicMock(), "extension": ".xz"},
        }
        default = get_default_compression(algorithms=mock_algos, initial_default="gzip")
        self.assertEqual(default, "gzip")

    def test_get_default_compression_fallback(self):
        """Test when initial default is unavailable, but a fallback ('bz2') is."""
        mock_algos = {
            "gzip": {"opener": None, "extension": ".gz"},
            "bz2": {"opener": MagicMock(), "extension": ".bz2"},
            "lzma": {"opener": None, "extension": ".xz"},
        }
        default = get_default_compression(algorithms=mock_algos, initial_default="gzip")
        self.assertEqual(default, "bz2")

    def test_get_default_compression_none_available(self):
        """Test when no compression algorithms are available."""
        mock_algos = {
            "gzip": {"opener": None, "extension": ".gz"},
            "bz2": {"opener": None, "extension": ".bz2"},
            "lzma": {"opener": None, "extension": ".xz"},
        }
        initial_default = "gzip"
        default = get_default_compression(
            algorithms=mock_algos, initial_default=initial_default
        )
        self.assertEqual(default, initial_default)
        self.assertFalse(
            is_compression_available(initial_default, algorithms=mock_algos)
        )


if __name__ == "__main__":
    unittest.main()
