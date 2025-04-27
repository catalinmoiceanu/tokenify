# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
# pylint: disable=unused-argument
import unittest
import sys
import gzip
import bz2
import lzma
import tempfile
import shutil
import os
import stat
from pathlib import Path
from io import BytesIO
from unittest.mock import patch, MagicMock

# Assuming config and file_writer are in src directory relative to tests
from src.file_writer import FileWriter
from src.config import COMPRESSION_ALGORITHMS, is_compression_available


# Helper function to handle potential permission errors during rmtree
def rmtree_onerror(func, path, exc_info):
    """Error handler for shutil.rmtree."""
    perm_errors = (PermissionError,)
    if (
        sys.platform == "win32"
        and isinstance(exc_info[1], OSError)
        and exc_info[1].winerror == 5  # Access is denied
    ):
        perm_errors += (OSError,)

    if isinstance(exc_info[1], perm_errors):
        path_str = str(path)
        try:
            current_mode = os.stat(path_str).st_mode
            os.chmod(
                path_str, current_mode | stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH
            )
            func(path_str)
        except Exception as e:
            # Re-raise original error if retry fails
            raise exc_info[1] from e
    else:
        raise exc_info[1]


class TestFileWriter(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_fw_"))
        self.test_data = b"Some test data\nwith multiple lines."
        self.read_only_dirs = []

    def tearDown(self):
        for dir_path in self.read_only_dirs:
            try:
                os.chmod(dir_path, 0o777)
            except OSError:
                pass  # Ignore errors during cleanup
        shutil.rmtree(self.test_dir, onerror=rmtree_onerror)

    # --- Init Tests ---
    def test_init_no_compression(self):
        writer = FileWriter()
        self.assertFalse(writer.compress)
        self.assertIsNone(writer.compression_algo)

    def test_init_compression_valid(self):
        algo = "gzip"
        if not is_compression_available(algo):
            self.skipTest(f"{algo} compression not available")
        settings = COMPRESSION_ALGORITHMS[algo]
        writer = FileWriter(
            compress=True, compression_algo=algo, compression_settings=settings
        )
        self.assertTrue(writer.compress)
        self.assertEqual(writer.compression_algo, algo)
        self.assertEqual(writer.compression_settings, settings)

    def test_init_compression_invalid_algo(self):
        mock_settings = {"opener": None, "extension": ".inv"}
        with self.assertRaisesRegex(
            ValueError, "Compression requested with algorithm 'invalid'"
        ):
            FileWriter(
                compress=True,
                compression_algo="invalid",
                compression_settings=mock_settings,
            )

    def test_init_compression_missing_settings(self):
        with self.assertRaisesRegex(ValueError, "settings.*missing/invalid"):
            FileWriter(
                compress=True,
                compression_algo="gzip",
                compression_settings={"extension": ".gz"},
            )
        with self.assertRaisesRegex(ValueError, "settings.*missing/invalid"):
            FileWriter(
                compress=True,
                compression_algo="gzip",
                compression_settings={"opener": gzip.open},
            )

    # --- Uncompressed Write Tests ---
    def test_write_uncompressed_to_file(self):
        writer = FileWriter()
        target_path = self.test_dir / "output.txt"
        writer.write(self.test_data, target_path)
        self.assertTrue(target_path.exists())
        with open(target_path, "rb") as f:
            self.assertEqual(f.read(), self.test_data)

    def test_write_uncompressed_to_file_creates_parents(self):
        writer = FileWriter()
        target_path = self.test_dir / "subdir" / "another_subdir" / "output.txt"
        writer.write(self.test_data, target_path)
        self.assertTrue(target_path.exists())
        self.assertTrue(target_path.parent.exists())
        self.assertTrue(target_path.parent.parent.exists())
        with open(target_path, "rb") as f:
            self.assertEqual(f.read(), self.test_data)

    def test_write_uncompressed_to_stdout(self):
        writer = FileWriter()
        mock_stdout_buffer = BytesIO()
        mock_stdout_wrapper = MagicMock(spec=sys.stdout)
        mock_stdout_wrapper.buffer = mock_stdout_buffer

        with patch("sys.stdout", mock_stdout_wrapper):
            writer.write(self.test_data, None)

        mock_stdout_buffer.seek(0)
        self.assertEqual(mock_stdout_buffer.read(), self.test_data)

    # --- Compressed Write Tests ---
    def _test_write_compressed_to_file(self, algo, opener, extension):
        """Helper to test writing compressed file."""
        if not is_compression_available(algo):
            self.skipTest(f"{algo} not available")

        settings = COMPRESSION_ALGORITHMS[algo]
        writer = FileWriter(
            compress=True, compression_algo=algo, compression_settings=settings
        )
        base_target_path = self.test_dir / f"output_{algo}.txt"
        expected_target_path = self.test_dir / f"output_{algo}.txt{extension}"

        writer.write(self.test_data, base_target_path)

        self.assertTrue(
            expected_target_path.exists(), f"{expected_target_path} was not created"
        )
        self.assertFalse(
            base_target_path.exists(), f"{base_target_path} should not exist"
        )

        with opener(expected_target_path, "rb") as f:
            self.assertEqual(f.read(), self.test_data)

    def test_write_compressed_gzip_to_file(self):
        self._test_write_compressed_to_file("gzip", gzip.open, ".gz")

    def test_write_compressed_bz2_to_file(self):
        self._test_write_compressed_to_file("bz2", bz2.open, ".bz2")

    def test_write_compressed_lzma_to_file(self):
        self._test_write_compressed_to_file("lzma", lzma.open, ".xz")

    def test_write_compressed_to_file_path_already_has_extension(self):
        """Test writing when target path already includes the compression extension."""
        algo = "gzip"
        if not is_compression_available(algo):
            self.skipTest(f"{algo} not available")

        opener = COMPRESSION_ALGORITHMS[algo]["opener"]
        extension = COMPRESSION_ALGORITHMS[algo]["extension"]
        settings = COMPRESSION_ALGORITHMS[algo]
        writer = FileWriter(
            compress=True, compression_algo=algo, compression_settings=settings
        )
        target_path_with_ext = self.test_dir / f"output_inplace.txt{extension}"

        writer.write(self.test_data, target_path_with_ext)

        self.assertTrue(target_path_with_ext.exists())
        with opener(target_path_with_ext, "rb") as f:
            self.assertEqual(f.read(), self.test_data)

    def _test_write_compressed_to_stdout(self, algo, opener, _extension):
        """Helper to test writing compressed data to stdout."""
        if not is_compression_available(algo):
            self.skipTest(f"{algo} not available")

        settings = COMPRESSION_ALGORITHMS[algo]
        writer = FileWriter(
            compress=True, compression_algo=algo, compression_settings=settings
        )

        mock_stdout_buffer = BytesIO()
        mock_stdout_wrapper = MagicMock(spec=sys.stdout)
        mock_stdout_wrapper.buffer = mock_stdout_buffer

        with patch("sys.stdout", mock_stdout_wrapper):
            writer.write(self.test_data, None)

        mock_stdout_buffer.seek(0)
        compressed_data = mock_stdout_buffer.read()
        self.assertTrue(compressed_data)

        with opener(BytesIO(compressed_data), "rb") as f:
            decompressed_data = f.read()
        self.assertEqual(decompressed_data, self.test_data)

    def test_write_compressed_gzip_to_stdout(self):
        self._test_write_compressed_to_stdout("gzip", gzip.open, ".gz")

    def test_write_compressed_bz2_to_stdout(self):
        self._test_write_compressed_to_stdout("bz2", bz2.open, ".bz2")

    def test_write_compressed_lzma_to_stdout(self):
        self._test_write_compressed_to_stdout("lzma", lzma.open, ".xz")

    # --- Error Handling Tests ---

    @patch("builtins.open", side_effect=IOError("Disk full"))
    def test_write_uncompressed_io_error(self, mock_open_builtin):
        """Test IOError during uncompressed file write."""
        writer = FileWriter()
        target_path = self.test_dir / "output_io_error.txt"
        with self.assertRaisesRegex(IOError, "Disk full"):
            writer.write(self.test_data, target_path)
        mock_open_builtin.assert_called_once_with(target_path, "wb")

    @patch("builtins.open", side_effect=OSError("Fake permission denied"))
    def test_write_compressed_io_error(self, mock_open):
        """Test OSError during compressed file write."""
        algo = "gzip"
        if not is_compression_available(algo):
            self.skipTest(f"{algo} not available")

        settings = COMPRESSION_ALGORITHMS[algo]
        writer = FileWriter(
            compress=True, compression_algo=algo, compression_settings=settings
        )
        target_path = self.test_dir / "output_compress_io_error.txt"

        with self.assertRaisesRegex(OSError, "Fake permission denied"):
            writer.write(self.test_data, target_path)

        expected_compressed_path = target_path.with_suffix(
            target_path.suffix + settings["extension"]
        )
        mock_open.assert_called_once_with(expected_compressed_path, "wb")

    @patch("builtins.open", side_effect=PermissionError("Mock permission denied"))
    def test_write_uncompressed_permission_error(self, mock_open_builtin):
        """Test PermissionError using mock."""
        writer = FileWriter()
        target_path = self.test_dir / "perm_denied_output.txt"

        with self.assertRaisesRegex(PermissionError, "Mock permission denied"):
            writer.write(self.test_data, target_path)

        mock_open_builtin.assert_called_once_with(target_path, "wb")


if __name__ == "__main__":
    unittest.main()
