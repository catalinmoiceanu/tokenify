# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
import unittest

# import sys # No longer needed
from unittest.mock import patch, MagicMock

# Import the main function and the CLI class it uses
import src.main

# from src.cli import CLI # No longer needed directly in tests


class TestMain(unittest.TestCase):

    @patch("src.main.CLI")
    @patch("sys.argv", ["main.py", "input.py"])
    def test_main_success(self, mock_cli_class):
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance

        src.main.main()

        mock_cli_class.assert_called_once_with()
        mock_cli_instance.run.assert_called_once_with(["input.py"])

    @patch("src.main.CLI")
    @patch("sys.argv", ["main.py", "-i", "input.py"])
    def test_main_with_args(self, mock_cli_class):
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance

        src.main.main()

        mock_cli_class.assert_called_once_with()
        mock_cli_instance.run.assert_called_once_with(["-i", "input.py"])

    @patch("src.main.CLI")
    @patch("sys.argv", ["main.py", "input.py"])
    @patch("sys.exit")
    def test_main_system_exit_0(self, mock_exit, mock_cli_class):
        mock_cli_instance = MagicMock()
        mock_cli_instance.run.side_effect = SystemExit(0)
        mock_cli_class.return_value = mock_cli_instance

        src.main.main()

        mock_cli_class.assert_called_once_with()
        mock_cli_instance.run.assert_called_once_with(["input.py"])
        mock_exit.assert_called_once_with(0)

    @patch("src.main.CLI")
    @patch("sys.argv", ["main.py", "--invalid-arg"])
    @patch("sys.exit")
    def test_main_system_exit_non_zero(self, mock_exit, mock_cli_class):
        mock_cli_instance = MagicMock()
        mock_cli_instance.run.side_effect = SystemExit(2)
        mock_cli_class.return_value = mock_cli_instance

        src.main.main()

        mock_cli_class.assert_called_once_with()
        mock_cli_instance.run.assert_called_once_with(["--invalid-arg"])
        mock_exit.assert_called_once_with(2)

    @patch("src.main.CLI")
    @patch("sys.argv", ["main.py", "input.py"])
    @patch("sys.exit")
    def test_main_unexpected_exception(self, mock_exit, mock_cli_class):
        mock_cli_instance = MagicMock()
        test_exception = ValueError("Something broke unexpectedly")
        mock_cli_instance.run.side_effect = test_exception
        mock_cli_class.return_value = mock_cli_instance

        src.main.main()

        mock_cli_class.assert_called_once_with()
        mock_cli_instance.run.assert_called_once_with(["input.py"])
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
