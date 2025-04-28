# pylint: disable=missing-module-docstring, redefined-outer-name, protected-access
import tokenize
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from src.file_processor import FileProcessor
from src.file_writer import FileWriter
INPUT_CONTENT = b"""# Comment
x = 1 # Inline
"""
STRIPPED_CONTENT = b"""
x = 1
"""
@pytest.fixture
def mock_writer(mocker) -> MagicMock:
    """Fixture to create a mock FileWriter."""
    mock = mocker.MagicMock(spec=FileWriter)
    return mock
@pytest.fixture
def sample_input_file(tmp_path: Path) -> Path:
    """Fixture to create a temporary input file."""
    input_file = tmp_path / "input.py"
    input_file.write_bytes(INPUT_CONTENT)
    return input_file
def test_init_success(sample_input_file: Path, mock_writer: MagicMock):
    """Test successful initialization."""
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    assert processor.input_path == sample_input_file
    assert processor.writer == mock_writer
def test_init_wrong_input_type(mock_writer: MagicMock):
    """Test TypeError if input_path is not a Path object."""
    with pytest.raises(TypeError, match="input_path must be a Path object"):
        FileProcessor(input_path="not_a_path", writer=mock_writer)  # type: ignore
def test_init_wrong_writer_type(sample_input_file: Path):
    """Test TypeError if writer is not a FileWriter instance."""
    with pytest.raises(TypeError, match="writer must be a FileWriter instance"):
        FileProcessor(input_path=sample_input_file, writer=object())  # type: ignore
@patch("src.file_processor.CommentStripper.strip", return_value=STRIPPED_CONTENT)
def test_process_success(
    mock_strip: MagicMock,
    sample_input_file: Path,
    mock_writer: MagicMock,
    tmp_path: Path,
):
    """Test the successful processing flow."""
    output_path = tmp_path / "output.py"
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    with patch.object(processor, "_read_file", return_value=INPUT_CONTENT) as mock_read:
        processor.process(output_path)
    mock_read.assert_called_once()
    mock_strip.assert_called_once_with(INPUT_CONTENT)
    mock_writer.write.assert_called_once_with(STRIPPED_CONTENT, output_path)
@patch("src.file_processor.CommentStripper.strip", return_value=STRIPPED_CONTENT)
def test_process_success_stdout(
    mock_strip: MagicMock, sample_input_file: Path, mock_writer: MagicMock
):
    """Test the successful processing flow writing to stdout."""
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    with patch.object(processor, "_read_file", return_value=INPUT_CONTENT) as mock_read:
        processor.process(None)
    mock_read.assert_called_once()
    mock_strip.assert_called_once_with(INPUT_CONTENT)
    mock_writer.write.assert_called_once_with(STRIPPED_CONTENT, None)
def test_process_read_file_not_found(mock_writer: MagicMock, tmp_path: Path):
    """Test FileNotFoundError during _read_file."""
    non_existent_file = tmp_path / "ghost.py"
    processor = FileProcessor(input_path=non_existent_file, writer=mock_writer)
    with pytest.raises(FileNotFoundError):
        processor.process(None)
    mock_writer.write.assert_not_called()
@patch(
    "src.file_processor.CommentStripper.strip",
    side_effect=tokenize.TokenError("Invalid token"),
)
def test_process_strip_token_error(
    mock_strip: MagicMock, sample_input_file: Path, mock_writer: MagicMock
):
    """Test TokenError during CommentStripper.strip."""
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    with patch.object(processor, "_read_file", return_value=INPUT_CONTENT) as mock_read:
        with pytest.raises(tokenize.TokenError, match="Invalid token"):
            processor.process(None)
    mock_read.assert_called_once()
    mock_strip.assert_called_once_with(INPUT_CONTENT)
    mock_writer.write.assert_not_called()
@patch("src.file_processor.CommentStripper.strip", return_value=STRIPPED_CONTENT)
def test_process_writer_io_error(
    mock_strip: MagicMock, sample_input_file: Path, mock_writer: MagicMock
):
    """Test IOError raised by the writer's write method."""
    mock_writer.write.side_effect = IOError("Disk full")
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    with patch.object(processor, "_read_file", return_value=INPUT_CONTENT) as mock_read:
        with pytest.raises(IOError, match="Disk full"):
            processor.process(None)
    mock_read.assert_called_once()
    mock_strip.assert_called_once_with(INPUT_CONTENT)
    mock_writer.write.assert_called_once_with(STRIPPED_CONTENT, None)
@patch("src.file_processor.CommentStripper.strip", return_value=STRIPPED_CONTENT)
def test_process_unexpected_error_during_read(
    mock_strip: MagicMock, sample_input_file: Path, mock_writer: MagicMock
):
    """Test handling of unexpected errors during read."""
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    with patch.object(
        processor, "_read_file", side_effect=RuntimeError("Unexpected read issue")
    ) as mock_read:
        with pytest.raises(RuntimeError, match="Unexpected read issue"):
            processor.process(None)
    mock_read.assert_called_once()
    mock_strip.assert_not_called()
    mock_writer.write.assert_not_called()
def test_read_file_success(sample_input_file: Path, mock_writer: MagicMock):
    """Test the internal _read_file method successfully reads content."""
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    content = processor._read_file()
    assert content == INPUT_CONTENT
def test_read_file_not_found(tmp_path: Path, mock_writer: MagicMock):
    """Test _read_file raises FileNotFoundError."""
    non_existent_file = tmp_path / "ghost.py"
    processor = FileProcessor(input_path=non_existent_file, writer=mock_writer)
    with pytest.raises(FileNotFoundError):
        processor._read_file()
@patch("builtins.open", side_effect=PermissionError("Permission denied"))
def test_read_file_permission_error(
    mock_open, sample_input_file: Path, mock_writer: MagicMock
):
    """Test _read_file raises PermissionError."""
    assert sample_input_file.exists()
    processor = FileProcessor(input_path=sample_input_file, writer=mock_writer)
    with pytest.raises(PermissionError):
        processor._read_file()
    mock_open.assert_called_once_with(sample_input_file, "rb")
