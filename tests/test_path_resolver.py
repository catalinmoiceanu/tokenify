# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# from unittest.mock import MagicMock # No longer needed

from src.path_resolver import PathResolver


class TestPathResolver(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / "file1.py").touch()
        (self.test_dir / "file2.txt").touch()
        (self.test_dir / "subdir1").mkdir()
        (self.test_dir / "subdir1" / "file3.py").touch()
        (self.test_dir / "subdir1" / "file4.pyc").touch()
        (self.test_dir / "subdir2").mkdir()
        (self.test_dir / "subdir2" / "file5.py").touch()
        (self.test_dir / "subdir1" / "another.py").touch()
        (self.test_dir / "subdir2" / "another.py").touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_gather_single_file_py(self):
        path = self.test_dir / "file1.py"
        expected = [path.resolve()]
        result = PathResolver.gather_python_files([str(path)])
        self.assertEqual(result, expected)

    def test_gather_single_file_non_py(self):
        path = self.test_dir / "file2.txt"
        expected = []
        result = PathResolver.gather_python_files([str(path)])
        self.assertEqual(result, expected)

    def test_gather_non_existent_file(self):
        path = self.test_dir / "nonexistent.py"
        expected = []
        result = PathResolver.gather_python_files([str(path)])
        self.assertEqual(result, expected)

    def test_gather_directory_recursive(self):
        path = self.test_dir
        expected = sorted(
            [
                (self.test_dir / "file1.py").resolve(),
                (self.test_dir / "subdir1" / "file3.py").resolve(),
                (self.test_dir / "subdir1" / "another.py").resolve(),
                (self.test_dir / "subdir2" / "file5.py").resolve(),
                (self.test_dir / "subdir2" / "another.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files([str(path)])
        self.assertEqual(result, expected)

    def test_gather_specific_directory(self):
        path = self.test_dir / "subdir1"
        expected = sorted(
            [
                (self.test_dir / "subdir1" / "file3.py").resolve(),
                (self.test_dir / "subdir1" / "another.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files([str(path)])
        self.assertEqual(result, expected)

    def test_gather_multiple_inputs(self):
        paths = [
            str(self.test_dir / "file1.py"),
            str(self.test_dir / "subdir2"),
            str(self.test_dir / "nonexistent.py"),
            str(self.test_dir / "file2.txt"),
        ]
        expected = sorted(
            [
                (self.test_dir / "file1.py").resolve(),
                (self.test_dir / "subdir2" / "file5.py").resolve(),
                (self.test_dir / "subdir2" / "another.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files(paths)
        self.assertEqual(result, expected)

    def test_gather_duplicates(self):
        paths = [
            str(self.test_dir / "file1.py"),
            str(self.test_dir / "file1.py"),
            str(self.test_dir),
        ]
        expected = sorted(
            [
                (self.test_dir / "file1.py").resolve(),
                (self.test_dir / "subdir1" / "file3.py").resolve(),
                (self.test_dir / "subdir1" / "another.py").resolve(),
                (self.test_dir / "subdir2" / "file5.py").resolve(),
                (self.test_dir / "subdir2" / "another.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files(paths)
        self.assertEqual(result, expected)

    def test_gather_glob_files(self):
        pattern = str(self.test_dir / "*.py")
        expected = sorted([(self.test_dir / "file1.py").resolve()])
        result = PathResolver.gather_python_files([pattern])
        self.assertEqual(result, expected)

    def test_gather_glob_recursive(self):
        pattern = str(self.test_dir / "**/*.py")
        expected = sorted(
            [
                (self.test_dir / "file1.py").resolve(),
                (self.test_dir / "subdir1" / "file3.py").resolve(),
                (self.test_dir / "subdir1" / "another.py").resolve(),
                (self.test_dir / "subdir2" / "file5.py").resolve(),
                (self.test_dir / "subdir2" / "another.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files([pattern])
        self.assertEqual(result, expected)

    def test_gather_glob_specific(self):
        pattern = str(self.test_dir / "subdir*/*.py")
        expected = sorted(
            [
                (self.test_dir / "subdir1" / "file3.py").resolve(),
                (self.test_dir / "subdir1" / "another.py").resolve(),
                (self.test_dir / "subdir2" / "file5.py").resolve(),
                (self.test_dir / "subdir2" / "another.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files([pattern])
        self.assertEqual(result, expected)

    def test_gather_glob_no_match(self):
        pattern = str(self.test_dir / "nomatch*.py")
        expected = []
        result = PathResolver.gather_python_files([pattern])
        self.assertEqual(result, expected)

    def test_gather_mixed_glob_and_direct(self):
        paths = [
            str(self.test_dir / "subdir1" / "*.py"),
            str(self.test_dir / "subdir2" / "file5.py"),
        ]
        expected = sorted(
            [
                (self.test_dir / "subdir1" / "file3.py").resolve(),
                (self.test_dir / "subdir1" / "another.py").resolve(),
                (self.test_dir / "subdir2" / "file5.py").resolve(),
            ]
        )
        result = PathResolver.gather_python_files(paths)
        self.assertEqual(result, expected)

    @patch("pathlib.Path.resolve", side_effect=OSError("Resolution failed"))
    def test_gather_resolve_error(self, mock_resolve):
        path = str(self.test_dir / "file1.py")
        expected = []
        result = PathResolver.gather_python_files([path])
        self.assertEqual(result, expected)
        mock_resolve.assert_called()

    @patch("pathlib.Path.exists", side_effect=OSError("Permission denied"))
    def test_gather_exists_error(self, mock_exists):
        path = str(self.test_dir / "file1.py")
        expected = []
        result = PathResolver.gather_python_files([path])
        self.assertEqual(result, expected)
        mock_exists.assert_called()

    @patch("glob.glob", side_effect=Exception("Glob error"))
    def test_gather_glob_error(self, mock_glob):
        pattern = str(self.test_dir / "*.py")
        expected = []
        result = PathResolver.gather_python_files([pattern])
        self.assertEqual(result, expected)
        mock_glob.assert_called_with(pattern, recursive=True)


if __name__ == "__main__":
    unittest.main()
