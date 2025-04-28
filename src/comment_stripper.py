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
            Exception: For unexpected errors during untokenizing or post-processing.
        """
        if not source_bytes:
            log.debug("Source bytes are empty, returning empty bytes.")
            return b""

        result_tokens: List[tokenize.TokenInfo] = []
        try:
            # --- Tokenization Phase ---
            source_buffer = BytesIO(source_bytes)
            # tokenize.tokenize itself can raise TokenError for certain issues
            # like encoding detection problems.
            g = tokenize.tokenize(source_buffer.readline)

            # Iterate through tokens, filtering comments
            # This loop is where encoding errors within lines typically occur.
            for tok in g:
                if tok.type == tokenize.COMMENT:
                    # Check if comment should be kept based on the pattern
                    if keep_pattern and keep_pattern.match(tok.string):
                        log.debug("Keeping comment matching pattern: %s", tok.string)
                        result_tokens.append(tok)
                    else:
                        log.debug("Removing comment: %s", tok.string)
                        continue # Skip adding removed comment
                else:
                    # Keep all non-comment tokens
                    result_tokens.append(tok)

        except tokenize.TokenError as e:
            # Catch TokenErrors raised directly by tokenize setup or certain token patterns
            log.error("Tokenization failed: %s", e)
            raise e
        except UnicodeDecodeError as e:
            # Explicitly catch UnicodeDecodeError from iterating the generator 'g'
            # (which happens inside tokenize._tokenize) and wrap it.
            log.error("Encoding error during tokenization: %s", e)
            raise tokenize.TokenError(f"Encoding error during tokenization: {e}") from e
        # Let other potential errors during token iteration (if any) propagate

        # --- Untokenize and Post-processing Phase ---
        try:
            if not result_tokens:
                intermediate_bytes = b""
            else:
                intermediate_bytes = tokenize.untokenize(result_tokens)

            # Decode for line processing.
            intermediate_string = intermediate_bytes.decode("utf-8", 'replace')

            lines = intermediate_string.splitlines() # Split without keepends
            processed_lines: List[str] = []

            for line in lines:
                stripped_line_content = line.strip()

                if remove_empty_lines:
                    # Keep only lines with actual content
                    if stripped_line_content:
                        processed_lines.append(line.rstrip())
                else:
                    # Keep all lines, clean up lines that became *only* whitespace
                    if not stripped_line_content:
                        processed_lines.append("") # Represent blank lines as empty strings
                    else:
                        processed_lines.append(line.rstrip()) # Keep content lines, remove trailing whitespace

            # Join lines with '\n' and add a single trailing '\n' if the result is not empty.
            if not processed_lines:
                 final_string = ""
            else:
                 final_string = "\n".join(processed_lines) + "\n"

            # Encode back to bytes
            cleaned_bytes = final_string.encode("utf-8")

            log.debug(
                "Stripped comments: original size=%d, final size=%d (keep_pattern=%s, remove_empty=%s)",
                len(source_bytes),
                len(cleaned_bytes),
                bool(keep_pattern),
                remove_empty_lines,
            )
            return cleaned_bytes

        except Exception as e:
            # Catch unexpected errors during untokenizing or post-processing
            log.error("Failed during untokenize/post-processing: %s", e)
            raise e