# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
# pylint: disable=unused-argument
import unittest
import sys
import tempfile
import shutil
import os
import stat
from pathlib import Path
from io import BytesIO
from unittest.mock import patch, MagicMock
from src.tokenify.file_writer import FileWriter
def rmtree_onerror(func, path, exc_info):
    """Error handler for shutil.rmtree."""
    perm_errors = (PermissionError,)
    if (
        sys.platform == "win32"
        and isinstance(exc_info[1], OSError)
        and exc_info[1].winerror == 5
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
                pass
        shutil.rmtree(self.test_dir, onerror=rmtree_onerror)
    def test_write_to_file(self):
        writer = FileWriter()
        target_path = self.test_dir / "output.txt"
        writer.write(self.test_data, target_path)
        self.assertTrue(target_path.exists())
        with open(target_path, "rb") as f:
            self.assertEqual(f.read(), self.test_data)
    def test_write_to_file_creates_parents(self):
        writer = FileWriter()
        target_path = self.test_dir / "subdir" / "another_subdir" / "output.txt"
        writer.write(self.test_data, target_path)
        self.assertTrue(target_path.exists())
        self.assertTrue(target_path.parent.exists())
        self.assertTrue(target_path.parent.parent.exists())
        with open(target_path, "rb") as f:
            self.assertEqual(f.read(), self.test_data)
    def test_write_to_stdout(self):
        writer = FileWriter()
        mock_stdout_buffer = BytesIO()
        mock_stdout_wrapper = MagicMock(spec=sys.stdout)
        mock_stdout_wrapper.buffer = mock_stdout_buffer
        with patch("sys.stdout", mock_stdout_wrapper):
            writer.write(self.test_data, None)
        mock_stdout_buffer.seek(0)
        self.assertEqual(mock_stdout_buffer.read(), self.test_data)
    @patch("builtins.open", side_effect=IOError("Disk full"))
    def test_write_io_error(self, mock_open_builtin):
        """Test IOError during file write."""
        writer = FileWriter()
        target_path = self.test_dir / "output_io_error.txt"
        with self.assertRaisesRegex(IOError, "Disk full"):
            writer.write(self.test_data, target_path)
        mock_open_builtin.assert_called_once_with(target_path, "wb")
if __name__ == "__main__":
    unittest.main()
