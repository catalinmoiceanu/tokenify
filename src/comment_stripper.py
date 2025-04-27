"""
Contains the CommentStripper class responsible for removing comments
from Python source code using tokenize/untokenize, with options to keep
specific comments and remove resulting empty lines.
"""
import tokenize
import logging
import re
from io import BytesIO
from typing import List, Optional, Pattern
log = logging.getLogger(__name__)
DEFAULT_KEEP_PATTERN = re.compile(r"#\s*(pylint:|flake8:|type:|noqa:)", re.IGNORECASE)
# pylint: disable=too-few-public-methods
class CommentStripper:
    """
    Strips comments from Python source code bytes, optionally keeping specific
    patterns and removing lines that become empty.
    """
    @staticmethod
    def strip(
        source_bytes: bytes,
        keep_pattern: Optional[Pattern[str]] = DEFAULT_KEEP_PATTERN,
        remove_empty_lines: bool = True,
    ) -> bytes:
        """
        Removes comment tokens from Python source code bytes using tokenize/untokenize.
        Args:
            source_bytes: The Python source code as bytes.
            keep_pattern: A compiled regex pattern. Comments matching this pattern
                          will be kept. If None, all comments are removed.
                          Defaults to matching common linter directives.
            remove_empty_lines: If True, lines that become empty (or contain only
                                whitespace) after comments are removed will also
                                be removed. Defaults to True.
        Returns:
            The cleaned source code as bytes.
        Raises:
            tokenize.TokenError: If the source code cannot be tokenized (includes decode errors).
            UnicodeDecodeError: If the source code cannot be decoded using UTF-8 during
                                the post-processing step (less likely).
            Exception: For unexpected errors during untokenizing or processing.
        """
        if not source_bytes:
            log.debug("Source bytes are empty, returning empty bytes.")
            return b""
        result_tokens: List[tokenize.TokenInfo] = []
        try:
            source_buffer = BytesIO(source_bytes)
            g = tokenize.tokenize(source_buffer.readline)
            for tok in g:
                if tok.type == tokenize.COMMENT:
                    if keep_pattern and keep_pattern.match(tok.string):
                        log.debug("Keeping comment matching pattern: %s", tok.string)
                        result_tokens.append(tok)
                    else:
                        log.debug("Removing comment: %s", tok.string)
                        continue
                else:
                    result_tokens.append(tok)
            if not result_tokens:
                intermediate_bytes = b""
            else:
                intermediate_bytes = tokenize.untokenize(result_tokens)
            try:
                intermediate_string = intermediate_bytes.decode("utf-8")
            except UnicodeDecodeError as e:
                log.error("Failed to decode intermediate bytes as UTF-8: %s", e)
                raise UnicodeDecodeError(
                    "utf-8",
                    intermediate_bytes,
                    e.start,
                    e.end,
                    f"Failed to decode as UTF-8 for post-processing: {e.reason}",
                ) from e
            lines = intermediate_string.splitlines()
            processed_lines: List[str] = []
            for line in lines:
                stripped_line = line.rstrip()
                if remove_empty_lines:
                    if stripped_line.strip():
                        processed_lines.append(stripped_line)
                else:
                    processed_lines.append(stripped_line)
            if not processed_lines:
                final_string = ""
            else:
                final_string = "\n".join(processed_lines)
                final_string += "\n"
            cleaned_bytes = final_string.encode("utf-8")
            log.debug(
                "Stripped comments: original size=%d, final size=%d (keep_pattern=%s, remove_empty=%s)",
                len(source_bytes),
                len(cleaned_bytes),
                bool(keep_pattern),
                remove_empty_lines,
            )
            return cleaned_bytes
        except (tokenize.TokenError, UnicodeDecodeError) as e:
            log.error("Failed to tokenize source: %s", e)
            raise tokenize.TokenError(f"Tokenization failed: {e}") from e
        except Exception as e:
            log.error("Failed during processing: %s", e)
            raise
