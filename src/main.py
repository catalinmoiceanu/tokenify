#!/usr/bin/env python3
# main.py
"""
Main entry point for the tokenify CLI application.

Sets up logging and invokes the CLI handler.
"""
import sys
import logging

from .cli import CLI

# Basic Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger(__name__)


def main() -> None:
    """Entry point function."""
    log.info("Tokenify application started.")
    cli_app = CLI()
    try:
        cli_app.run(sys.argv[1:])
        log.info("Tokenify application finished successfully.")
    except SystemExit as e:
        exit_code = getattr(e, "code", 1)
        if exit_code == 0:
            log.debug("Application exiting with status code: 0")
        elif exit_code == 2:
            log.error("Application exiting due to argument parsing error (code: 2).")
        else:
            # Use lazy formatting
            log.warning("Application exiting with status code: %s", exit_code)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log.warning("Application interrupted by user (KeyboardInterrupt).")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:  # Catch specific exceptions if identifiable, else keep broad
        # W0718: Catching broad Exception is sometimes necessary at the top level.
        # Consider adding specific catches if known critical errors can occur here.
        # Use lazy formatting
        log.critical(
            "Unexpected critical error in main execution flow: %s",
            e,
            exc_info=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
