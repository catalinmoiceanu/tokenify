# comment_stripper.py
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

# Default pattern for comments to keep (e.g., linter directives)
# Matches '#', optional whitespace, 'pylint:', 'flake8:', 'type:', 'noqa:', etc.
DEFAULT_KEEP_PATTERN = re.compile(r"#\s*(pylint:|flake8:|type:|noqa:)", re.IGNORECASE)


# R0903: Too few public methods is acceptable here for a utility class.
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
            # Use BytesIO to treat bytes as a file for readline
            source_buffer = BytesIO(source_bytes)
            # detect_encoding is implicitly called by tokenize.tokenize
            g = tokenize.tokenize(source_buffer.readline)

            for tok in g:
                # Check if the token is a comment
                if tok.type == tokenize.COMMENT:
                    # If a keep_pattern is provided and the comment matches, keep it
                    if keep_pattern and keep_pattern.match(tok.string):
                        log.debug("Keeping comment matching pattern: %s", tok.string)
                        result_tokens.append(tok)
                    else:
                        # Otherwise, skip (remove) the comment
                        log.debug("Removing comment: %s", tok.string)
                        continue  # Skip appending this token
                else:
                    # Keep all non-comment tokens
                    result_tokens.append(tok)

            # Untokenize the filtered list back into bytes
            if not result_tokens:
                intermediate_bytes = b""
            else:
                intermediate_bytes = tokenize.untokenize(result_tokens)

            # --- Post-processing ---
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

            # Split into lines for processing
            lines = intermediate_string.splitlines()
            processed_lines: List[str] = []

            # Process each line
            for line in lines:
                # Remove *only* trailing whitespace, preserving leading indentation
                stripped_line = line.rstrip()
                if remove_empty_lines:
                    # If removing empty lines, only keep lines with actual content
                    if stripped_line.strip():
                        processed_lines.append(stripped_line)
                else:
                    # If keeping empty lines, keep the line (even if blank after rstrip)
                    processed_lines.append(stripped_line)

            # Reconstruct the final string
            if not processed_lines:
                # Handle cases where the result is completely empty
                # Example: Input only comments, remove_empty_lines=True
                # Example: Input empty string b""
                # Example: Input just newline, remove_empty_lines=True
                final_string = ""
            else:
                # Join the processed lines
                final_string = "\n".join(processed_lines)
                # Add a single trailing newline if there's content
                final_string += "\n"

            # Encode the final string back to bytes
            cleaned_bytes = final_string.encode("utf-8")
            # --- End of post-processing ---

            log.debug(
                "Stripped comments: original size=%d, final size=%d (keep_pattern=%s, remove_empty=%s)",
                len(source_bytes),
                len(cleaned_bytes),
                bool(keep_pattern),
                remove_empty_lines,
            )
            return cleaned_bytes

        # Catch errors during the tokenization phase itself
        except (tokenize.TokenError, UnicodeDecodeError) as e:
            log.error("Failed to tokenize source: %s", e)
            raise tokenize.TokenError(f"Tokenization failed: {e}") from e
        except Exception as e:
            log.error("Failed during processing: %s", e)
            raise
