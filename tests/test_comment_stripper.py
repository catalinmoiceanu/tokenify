# pylint: disable=missing-module-docstring, too-many-positional-arguments, missing-class-docstring, missing-function-docstring
import unittest
import tokenize
import re
from typing import Optional, Pattern
from src.comment_stripper import CommentStripper, DEFAULT_KEEP_PATTERN
# pylint: disable=too-many-public-methods
class TestCommentStripper(unittest.TestCase):
    """Test suite for the CommentStripper class."""
    # pylint: disable=invalid-name, too-many-arguments
    def assert_stripped_code_equal(
        self,
        source: bytes,
        expected_output: bytes,
        keep_pattern: Optional[Pattern[str]] = DEFAULT_KEEP_PATTERN,
        remove_empty_lines: bool = True,
        msg: Optional[str] = None,
    ):
        """
        Asserts that CommentStripper.strip(source) equals the expected output.
        Includes more detailed failure messages.
        """
        # pylint: disable=broad-exception-caught
        try:
            actual_output = CommentStripper.strip(
                source,
                keep_pattern=keep_pattern,
                remove_empty_lines=remove_empty_lines
            )
        except Exception as e:
            self.fail(
                f"CommentStripper.strip raised unexpected Exception: {e}\n{msg or ''}"
            )
        self.assertMultiLineEqual(
            actual_output.decode('utf-8', 'replace'),
            expected_output.decode('utf-8', 'replace'),
            msg=msg
        )
        self.assertEqual(actual_output, expected_output, msg=msg)
    def test_strip_no_comments(self):
        """Test stripping code with no comments."""
        source = b"print('Hello')\nx = 10"
        expected = b"print('Hello')\nx = 10\n"
        self.assert_stripped_code_equal(source, expected)
    def test_strip_hash_comments_removed(self):
        """Test stripping code with hash comments."""
        source = (
            b"# This is a comment\n"
            b"print('Hello') # Inline comment\n"
            b"x = 10 # Another one"
        )
        expected = b"print('Hello')\nx = 10\n"
        self.assert_stripped_code_equal(source, expected)
    def test_strip_multiline_string_not_comment(self):
        """Test that multiline strings are not treated as comments."""
        source = b"'''This is not\na comment'''\nprint('Hi')"
        expected = b"'''This is not\na comment'''\nprint('Hi')\n"
        self.assert_stripped_code_equal(source, expected)
    def test_strip_empty_input(self):
        """Test stripping empty input bytes."""
        source = b""
        expected = b""
        self.assert_stripped_code_equal(source, expected)
    def test_strip_only_comments_removed_empty_lines(self):
        """Test stripping input containing only comments (remove empty lines)."""
        source = b"# Line 1\n# Line 2\n    # Indented comment"
        expected = b""
        self.assert_stripped_code_equal(source, expected)
    def test_strip_only_comments_keep_empty_lines(self):
        """Test stripping input containing only comments (keep empty lines)."""
        source = b"# Line 1\n# Line 2\n    # Indented comment\n"
        expected = b"\n\n\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=False)
    def test_strip_only_comments_keep_empty_lines_no_trailing_nl(self):
        """Test stripping input containing only comments (keep empty, no trail nl)."""
        source = b"# Line 1\n# Line 2\n    # Indented comment"
        expected = b"\n\n\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=False)
    def test_strip_with_encoding_declaration(self):
        """Test stripping code with an encoding declaration comment."""
        source = b"# -*- coding: utf-8 -*-\nprint('Hello') # Comment"
        expected = b"print('Hello')\n"
        self.assert_stripped_code_equal(source, expected)
    def test_strip_complex_code_removed_empty_lines(self):
        """Test stripping complex code (remove empty lines)."""
        source = b"""
# Module comment
import os # Import os
# Function definition comment line 1
# Function definition comment line 2
def greet(name): # Takes name
    # Print greeting comment line 1
    # Print greeting comment line 2
    print(f"Hello, {name}!") # Formatted print
# After print comment
# After print comment 2
greet("World") # Call function
# Final comment line
"""
        expected = b"""import os
def greet(name):
    print(f"Hello, {name}!")
greet("World")
"""
        self.assert_stripped_code_equal(source, expected)
    def test_strip_invalid_token(self):
        """Test stripping code with invalid byte sequence."""
        source = b"a = 1\n\x80b = 2"
        with self.assertRaises(tokenize.TokenError):
            CommentStripper.strip(source)
    def test_strip_preserves_newlines_between_code(self):
        """Test blank lines between code when removing empty lines."""
        source = b"x = 1\n\n# comment\n\ny = 2"
        expected = b"x = 1\ny = 2\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=True)
    def test_strip_preserves_newlines_between_code_keep_empty(self):
        """Test blank lines between code when keeping empty lines."""
        source = b"x = 1\n\n# comment\n\ny = 2"
        expected = b"x = 1\n\n\n\ny = 2\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=False)
    def test_keep_pylint_comment(self):
        """Test keeping a pylint directive comment."""
        source = b"class MyClass:\n    pass # pylint: disable=too-few-public-methods"
        expected = b"class MyClass:\n    pass # pylint: disable=too-few-public-methods\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=DEFAULT_KEEP_PATTERN, remove_empty_lines=True
        )
    def test_keep_noqa_comment(self):
        """Test keeping a noqa directive comment."""
        source = b"import os, sys # noqa: E401"
        expected = b"import os, sys # noqa: E401\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=DEFAULT_KEEP_PATTERN, remove_empty_lines=True
        )
    def test_remove_regular_comment_keep_pylint(self):
        """Test removing regular comments while keeping pylint directives."""
        source = b"# Regular comment\nclass C:\n    pass # pylint: disable=C0115"
        expected = b"class C:\n    pass # pylint: disable=C0115\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=DEFAULT_KEEP_PATTERN, remove_empty_lines=True
        )
    def test_keep_comment_no_pattern(self):
        """Test removing all comments when keep_pattern is None."""
        source = b"# Regular comment\nx = 1 # pylint: disable=C0103"
        expected = b"x = 1\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=None, remove_empty_lines=True
        )
    def test_keep_custom_pattern_comment(self):
        """Test keeping comments matching a custom pattern."""
        source = b"# MY_CUSTOM_DIRECTIVE\nx = 1 # Regular comment"
        custom_pattern = re.compile(r"#\s*MY_CUSTOM_DIRECTIVE")
        expected = b"# MY_CUSTOM_DIRECTIVE\nx = 1\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=custom_pattern, remove_empty_lines=True
        )
    def test_line_with_only_kept_comment_remains(self):
        """Test that a line with only a kept comment remains."""
        source = b"x = 1\n# pylint: disable=invalid-name\ny = 2"
        expected = b"x = 1\n# pylint: disable=invalid-name\ny = 2\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=DEFAULT_KEEP_PATTERN, remove_empty_lines=True
        )
    def test_line_with_only_removed_comment_is_removed(self):
        """Test that a line with only a removed comment is removed."""
        source = b"x = 1\n# This comment will be removed\ny = 2"
        expected = b"x = 1\ny = 2\n"
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=DEFAULT_KEEP_PATTERN, remove_empty_lines=True
        )
    def test_mixed_comments_and_empty_line_removal(self):
        """Test mixed comments with empty line removal."""
        source = b"""
# Remove this line
code1 = 1 # Remove this comment
# pylint: disable=something
# Remove this line too
code2 = 2
"""
        expected = b"""code1 = 1
# pylint: disable=something
code2 = 2
"""
        self.assert_stripped_code_equal(
            source, expected, keep_pattern=DEFAULT_KEEP_PATTERN, remove_empty_lines=True
        )
    def test_preserve_final_newline_if_present(self):
        """Test that a final newline is preserved if present."""
        source = b"x = 1\n# comment\n"
        expected = b"x = 1\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=True)
    def test_add_final_newline_if_not_present(self):
        """Test that a final newline is added if not present."""
        source = b"x = 1"
        expected = b"x = 1\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=True)
    def test_input_is_just_newline(self):
        """Test input that is only a newline (remove empty)."""
        source = b"\n"
        expected = b""
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=True)
    def test_input_is_just_newline_keep_empty(self):
        """Test input that is only a newline (keep empty)."""
        source = b"\n"
        expected = b"\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=False)
    def test_input_is_just_kept_comment(self):
        """Test input that is only a kept comment."""
        source = b"# pylint: disable=abc\n"
        expected = b"# pylint: disable=abc\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=True)
    def test_input_is_just_removed_comment(self):
        """Test input that is only a removed comment (remove empty)."""
        source = b"# regular comment\n"
        expected = b""
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=True)
    def test_input_is_just_removed_comment_keep_empty(self):
        """Test input that is only a removed comment (keep empty)."""
        source = b"# regular comment\n"
        expected = b"\n"
        self.assert_stripped_code_equal(source, expected, remove_empty_lines=False)
if __name__ == "__main__":
    unittest.main()
