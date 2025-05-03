# pylint: disable=too-many-lines,missing-module-docstring,too-many-public-methods
import unittest
import tempfile
import shutil
import logging
import argparse
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock, call, ANY
from src.tokenify.cli import CLI, CLIRunner, OutputSettings
MOCK_PATH_RESOLVER = MagicMock()
MOCK_FILE_WRITER = MagicMock()
MOCK_FILE_PROCESSOR = MagicMock()
MOCK_GLOB = MagicMock()
MOCK_OS_PATH_COMMONPATH = MagicMock()
MOCK_OS_UNLINK = MagicMock()
@patch("src.tokenify.cli.PathResolver", MOCK_PATH_RESOLVER)
@patch("src.tokenify.cli.FileWriter", MOCK_FILE_WRITER)
@patch("src.tokenify.cli.FileProcessor", MOCK_FILE_PROCESSOR)
@patch("glob.glob", MOCK_GLOB)
@patch("src.tokenify.cli.os.path.commonpath", MOCK_OS_PATH_COMMONPATH)
@patch("src.tokenify.cli.os.unlink", MOCK_OS_UNLINK)
class TestCLI(unittest.TestCase):
    """Tests for the CLI and CLIRunner classes."""
    # pylint: disable=too-many-instance-attributes
    def setUp(self):
        """Set up test environment."""
        self.cli = CLI()
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_dir_resolved = self.test_dir.resolve()
        self.file1_resolved = (self.test_dir_resolved / "file1.py").resolve()
        self.file2_resolved = (self.test_dir_resolved / "subdir" / "file2.py").resolve()
        self.file1_resolved.parent.mkdir(parents=True, exist_ok=True)
        self.file1_resolved.touch()
        self.file2_resolved.parent.mkdir(parents=True, exist_ok=True)
        self.file2_resolved.touch()
        for mock_obj in [
            MOCK_PATH_RESOLVER,
            MOCK_FILE_WRITER,
            MOCK_FILE_PROCESSOR,
            MOCK_GLOB,
            MOCK_OS_PATH_COMMONPATH,
            MOCK_OS_UNLINK,
        ]:
            mock_obj.reset_mock()
        MOCK_PATH_RESOLVER.gather_python_files.return_value = [
            self.file1_resolved,
            self.file2_resolved,
        ]
        MOCK_OS_PATH_COMMONPATH.return_value = str(self.test_dir_resolved)
        MOCK_GLOB.return_value = []
        self.mock_processor_instance = MagicMock()
        self.mock_processor_instance.process.side_effect = None
        MOCK_FILE_PROCESSOR.return_value = self.mock_processor_instance
        logging.disable(logging.CRITICAL)
        self.stderr_patch = patch("sys.stderr", new_callable=StringIO)
        self.mock_stderr = self.stderr_patch.start()
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir_resolved, ignore_errors=True)
        logging.disable(logging.NOTSET)
        self.stderr_patch.stop()
    def _create_runner(self, cli_args_list: list) -> CLIRunner:
        """Helper to create a CLIRunner instance with mock args."""
        try:
            parsed_args = self.cli.parser.parse_args(cli_args_list)
            return CLIRunner(parsed_args)
        except argparse.ArgumentError:
            return CLIRunner(None)
    def test_parse_basic(self):
        """Test basic argument parsing."""
        args = self.cli.parser.parse_args([str(self.file1_resolved)])
        self.assertEqual(args.paths, [str(self.file1_resolved)])
        self.assertFalse(args.in_place)
        self.assertIsNone(args.output_dir)
        self.assertFalse(args.quiet)
        self.assertFalse(args.verbose)
    def test_parse_multiple_paths(self):
        """Test parsing multiple input paths."""
        args = self.cli.parser.parse_args(
            [str(self.file1_resolved), str(self.test_dir_resolved)]
        )
        self.assertEqual(
            args.paths, [str(self.file1_resolved), str(self.test_dir_resolved)]
        )
    def test_parse_in_place(self):
        """Test parsing the in-place flag."""
        args = self.cli.parser.parse_args(["-i", str(self.file1_resolved)])
        self.assertTrue(args.in_place)
    def test_parse_output_dir(self):
        """Test parsing the output directory argument."""
        out_dir = self.test_dir_resolved / "out"
        args = self.cli.parser.parse_args(
            ["-o", str(out_dir), str(self.file1_resolved)]
        )
        self.assertEqual(args.output_dir, out_dir)
    @patch("sys.exit")
    def test_run_handles_parse_error(self, mock_exit):
        """Test that run() handles parsing errors and exits."""
        temp_cli = CLI()
        temp_cli.run(["-z", "-a", "invalid", str(self.file1_resolved)])
        mock_exit.assert_any_call(2)
    def test_parse_quiet(self):
        """Test parsing the quiet flag."""
        args = self.cli.parser.parse_args(["-q", str(self.file1_resolved)])
        self.assertTrue(args.quiet)
    def test_parse_verbose(self):
        """Test parsing the verbose flag."""
        args = self.cli.parser.parse_args(["-v", str(self.file1_resolved)])
        self.assertTrue(args.verbose)
    @patch("sys.exit")
    def test_run_handles_missing_path(self, mock_exit):
        """Test that run() handles missing path arguments and exits."""
        self.cli.run([])
        mock_exit.assert_any_call(2)
    @patch("logging.getLogger")
    def test_setup_logging_default(self, mock_get_logger):
        """Test default logging setup (INFO level)."""
        mock_root = MagicMock()
        mock_handler = MagicMock()
        mock_root.handlers = [mock_handler]
        mock_root.hasHandlers.return_value = True
        mock_get_logger.return_value = mock_root
        runner = self._create_runner([str(self.file1_resolved)])
        # pylint: disable=protected-access
        runner._setup_logging()
        mock_root.setLevel.assert_called_with(logging.INFO)
        mock_handler.setLevel.assert_called_with(logging.INFO)
    @patch("logging.getLogger")
    def test_setup_logging_quiet(self, mock_get_logger):
        """Test quiet logging setup (WARNING level)."""
        mock_root = MagicMock()
        mock_handler = MagicMock()
        mock_root.handlers = [mock_handler]
        mock_root.hasHandlers.return_value = True
        mock_get_logger.return_value = mock_root
        runner = self._create_runner(["-q", str(self.file1_resolved)])
        # pylint: disable=protected-access
        runner._setup_logging()
        mock_root.setLevel.assert_called_with(logging.WARNING)
        mock_handler.setLevel.assert_called_with(logging.WARNING)
    @patch("logging.getLogger")
    def test_setup_logging_verbose(self, mock_get_logger):
        """Test verbose logging setup (DEBUG level)."""
        mock_root = MagicMock()
        mock_handler = MagicMock()
        mock_root.handlers = [mock_handler]
        mock_root.hasHandlers.return_value = True
        mock_get_logger.return_value = mock_root
        runner = self._create_runner(["-v", str(self.file1_resolved)])
        # pylint: disable=protected-access
        runner._setup_logging()
        mock_root.setLevel.assert_called_with(logging.DEBUG)
        mock_handler.setLevel.assert_called_with(logging.DEBUG)
    def test_validate_output_dir_exists(self):
        """Test validating an existing output directory."""
        out_dir = self.test_dir_resolved / "out"
        out_dir.mkdir()
        runner = self._create_runner(["-o", str(out_dir), str(self.file1_resolved)])
        # pylint: disable=protected-access
        validated_dir = runner._validate_output_dir()
        self.assertEqual(validated_dir, out_dir.resolve())
    def test_validate_output_dir_creates(self):
        """Test validating and creating a new output directory."""
        out_dir = self.test_dir_resolved / "out_new"
        runner = self._create_runner(["-o", str(out_dir), str(self.file1_resolved)])
        # pylint: disable=protected-access
        validated_dir = runner._validate_output_dir()
        self.assertEqual(validated_dir, out_dir.resolve())
        self.assertTrue(out_dir.exists())
        self.assertTrue(out_dir.is_dir())
    def test_validate_output_dir_is_file(self):
        """Test validation fails if output directory path is a file."""
        out_file = self.test_dir_resolved / "out_file"
        out_file.touch()
        runner = self._create_runner(["-o", str(out_file), str(self.file1_resolved)])
        with self.assertRaises(SystemExit) as cm:
            # pylint: disable=protected-access
            runner._validate_output_dir()
        self.assertEqual(cm.exception.code, 1)
    @patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied"))
    def test_validate_output_dir_permission_error(self, _mock_mkdir):
        """Test validation fails on permission error during directory creation."""
        out_dir = self.test_dir_resolved / "out_perm"
        runner = self._create_runner(["-o", str(out_dir), str(self.file1_resolved)])
        with self.assertRaises(SystemExit) as cm:
            # pylint: disable=protected-access
            runner._validate_output_dir()
        self.assertEqual(cm.exception.code, 1)
    def test_validate_in_place_overrides_output(self):
        """Test that in-place flag overrides output directory."""
        out_dir = self.test_dir_resolved / "out"
        runner = self._create_runner(
            ["-i", "-o", str(out_dir), str(self.file1_resolved)]
        )
        # pylint: disable=protected-access
        validated_dir = runner._validate_output_dir()
        self.assertIsNone(validated_dir)
    def test_determine_base_path_single_file(self):
        """Test determining base path for a single file input."""
        runner = self._create_runner([str(self.file1_resolved)])
        runner.input_files = [self.file1_resolved]
        # pylint: disable=protected-access
        runner._determine_base_path()
        self.assertEqual(runner.base_common_path, self.file1_resolved.parent)
    def test_determine_base_path_single_dir(self):
        """Test determining base path for a single directory input."""
        runner = self._create_runner([str(self.test_dir_resolved)])
        runner.input_files = [self.file1_resolved, self.file2_resolved]
        MOCK_OS_PATH_COMMONPATH.return_value = str(self.test_dir_resolved)
        # pylint: disable=protected-access
        runner._determine_base_path()
        self.assertEqual(runner.base_common_path, self.test_dir_resolved)
    def test_determine_base_path_multiple_files_same_dir(self):
        """Test determining base path for multiple files in the same directory."""
        file1a_resolved = (self.test_dir_resolved / "file1a.py").resolve()
        file1a_resolved.touch()
        runner = self._create_runner([str(self.file1_resolved), str(file1a_resolved)])
        runner.input_files = [self.file1_resolved, file1a_resolved]
        MOCK_OS_PATH_COMMONPATH.return_value = str(self.test_dir_resolved)
        # pylint: disable=protected-access
        runner._determine_base_path()
        self.assertEqual(runner.base_common_path, self.test_dir_resolved)
    def test_determine_base_path_files_different_dirs(self):
        """Test determining base path for files in different directories."""
        MOCK_OS_PATH_COMMONPATH.return_value = str(self.test_dir_resolved)
        runner = self._create_runner(
            [str(self.file1_resolved), str(self.file2_resolved)]
        )
        runner.input_files = [self.file1_resolved, self.file2_resolved]
        # pylint: disable=protected-access
        runner._determine_base_path()
        self.assertEqual(runner.base_common_path, self.test_dir_resolved)
        expected_commonpath_arg = [
            str(self.file1_resolved.resolve()),
            str(self.file2_resolved.resolve()),
        ]
        MOCK_OS_PATH_COMMONPATH.assert_called_once_with(expected_commonpath_arg)
    @patch("os.path.commonpath", side_effect=ValueError("Mock commonpath error"))
    def test_determine_base_path_commonpath_error(self, _mock_commonpath_err):
        """Test fallback behavior when os.path.commonpath raises an error."""
        runner = self._create_runner(
            [str(self.file1_resolved), str(self.file2_resolved)]
        )
        runner.input_files = [self.file1_resolved, self.file2_resolved]
        # pylint: disable=protected-access
        runner._determine_base_path()
        self.assertEqual(runner.base_common_path, self.file1_resolved.resolve().parent)
    @patch("pathlib.Path.resolve", lambda self: self)
    def test_get_output_destination_in_place_no_compress(self):
        """Test output destination for in-place, no compression."""
        runner = self._create_runner(["-i", str(self.file1_resolved)])
        runner.base_common_path = self.test_dir_resolved
        settings = OutputSettings(
            in_place=True,
            output_dir=None,
            base_common_path=runner.base_common_path,
        )
        # pylint: disable=protected-access
        base, log_path = runner._get_output_destination(self.file1_resolved, settings)
        self.assertEqual(base, self.file1_resolved)
        self.assertEqual(log_path, self.file1_resolved)
    @patch("pathlib.Path.resolve", lambda self: self)
    def test_get_output_destination_output_dir(self):
        """Test output destination for output directory, no compression."""
        out_dir = self.test_dir_resolved / "output"
        runner = self._create_runner(["-o", str(out_dir), str(self.file2_resolved)])
        runner.output_dir = out_dir
        runner.base_common_path = self.test_dir_resolved
        settings = OutputSettings(
            in_place=False,
            output_dir=runner.output_dir,
            base_common_path=runner.base_common_path,
        )
        # pylint: disable=protected-access
        base, log_path = runner._get_output_destination(self.file2_resolved, settings)
        expected_path = runner.output_dir / self.file2_resolved.relative_to(
            runner.base_common_path
        )
        self.assertEqual(base, expected_path)
        self.assertEqual(log_path, expected_path)
    @patch("pathlib.Path.resolve", lambda self: self)
    def test_get_output_destination_file_outside_base(self):
        """Test output destination for a file outside the calculated base path."""
        out_dir = self.test_dir_resolved / "output"
        other_file = Path("/elsewhere/other.py")
        runner = self._create_runner(["-o", str(out_dir), str(other_file)])
        runner.output_dir = out_dir
        runner.base_common_path = self.test_dir_resolved
        settings = OutputSettings(
            in_place=False,
            output_dir=runner.output_dir,
            base_common_path=runner.base_common_path,
        )
        # pylint: disable=protected-access
        base, log_path = runner._get_output_destination(other_file, settings)
        expected_path = runner.output_dir / other_file.name
        self.assertEqual(base, expected_path)
        self.assertEqual(log_path, expected_path)
    @patch("sys.exit")
    def test_run_simple(self, mock_exit):
        """Test the basic run workflow."""
        args = [str(self.file1_resolved), str(self.file2_resolved)]
        self.cli.run(args)
        MOCK_PATH_RESOLVER.gather_python_files.assert_called_once_with(
            [str(self.file1_resolved), str(self.file2_resolved)]
        )
        self.assertEqual(MOCK_FILE_PROCESSOR.call_count, 2)
        self.assertEqual(MOCK_FILE_WRITER.call_count, 2)
        proc_calls = MOCK_FILE_PROCESSOR.call_args_list
        expected_proc_calls = [
            call(input_path=self.file1_resolved, writer=ANY),
            call(input_path=self.file2_resolved, writer=ANY),
        ]
        self.assertCountEqual(proc_calls, expected_proc_calls)
        process_calls = self.mock_processor_instance.process.call_args_list
        expected_process_calls = [call(None), call(None)]
        self.assertCountEqual(process_calls, expected_process_calls)
        mock_exit.assert_called_once_with(0)
    @patch("sys.exit")
    def test_run_output_dir(self, mock_exit):
        """Test run with an output directory specified."""
        out_dir = self.test_dir_resolved / "out"
        args = ["-o", str(out_dir), str(self.file1_resolved), str(self.file2_resolved)]
        self.cli.run(args)
        MOCK_PATH_RESOLVER.gather_python_files.assert_called_once_with(
            [str(self.file1_resolved), str(self.file2_resolved)]
        )
        self.assertEqual(MOCK_FILE_PROCESSOR.call_count, 2)
        resolved_out_dir = out_dir.resolve()
        common_base = Path(MOCK_OS_PATH_COMMONPATH.return_value).resolve()
        expected_out1 = resolved_out_dir / self.file1_resolved.relative_to(common_base)
        expected_out2 = resolved_out_dir / self.file2_resolved.relative_to(common_base)
        expected_process_calls = [call(expected_out1), call(expected_out2)]
        self.assertCountEqual(
            self.mock_processor_instance.process.call_args_list, expected_process_calls
        )
        mock_exit.assert_called_once_with(0)
    @patch("sys.exit")
    def test_run_no_files_found(self, mock_exit):
        """Test run when no input files are found."""
        MOCK_PATH_RESOLVER.gather_python_files.return_value = []
        non_existent_path = str(self.test_dir_resolved / "nonexistent")
        args = [non_existent_path]
        self.cli.run(args)
        MOCK_PATH_RESOLVER.gather_python_files.assert_called_once_with(
            [non_existent_path]
        )
        MOCK_FILE_PROCESSOR.assert_not_called()
        mock_exit.assert_called_once_with(1)
    @patch("sys.exit")
    def test_run_processor_error(self, mock_exit):
        """Test run when the file processor encounters an error."""
        self.mock_processor_instance.process.side_effect = [
            None,
            IOError("Mock Write failed"),
        ]
        args = [str(self.file1_resolved), str(self.file2_resolved)]
        self.cli.run(args)
        self.assertEqual(self.mock_processor_instance.process.call_count, 2)
        mock_exit.assert_called_once_with(1)
if __name__ == "__main__":
    unittest.main()
