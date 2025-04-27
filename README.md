# tokenify

> A CLI tool to strip unnecessary comments (and optionally compress) from Python files.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🔍 Overview

`tokenify` helps you clean up Python code by removing standalone and inline comments, preserving shebangs and encoding lines, and optionally compressing output files. It supports:

- Directories (recursive scan).
- Individual `.py` files.
- Shell glob patterns (e.g. `src/**/*.py`).

## 🚀 Features

- **Strip comments**: removes all `#` comments while keeping code structure intact.
- **Compression**: optionally compress output using gzip, bz2, or lzma.
- **Flexible output**: in-place modification, custom output directory, or STDOUT.
- **Cross-platform**: runs anywhere Python 3.7+ is available.

## 🛠️ Requirements

- **Python** >= 3.7 (no external dependencies; all features use the standard library).

## 🏗️ Development Setup

Before installing `tokenify`, create and activate a virtual environment to isolate dependencies:

```bash
# Create a new environment
python3 -m venv .venv

# Activate on macOS/Linux
source .venv/bin/activate

# Or on Windows (PowerShell)
# .venv\Scripts\Activate.ps1

# Upgrade pip
pip install --upgrade pip
```

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/catalinmoiceanu/tokenify.git
cd tokenify

# Install as an editable package
pip install --user -e src
```

This will install a `tokenify` command in your `~/.local/bin` (or equivalent). Ensure that directory is on your `PATH`.

Alternatively, after publishing to PyPI:

```bash
pip install tokenify
```

## ⚙️ Usage

```shell
# View help
tokenify --help

# Strip comments from a single file (prints to stdout)
tokenify script.py

# Modify files in place across a directory
tokenify -i project/

# Write cleaned output to a separate folder
tokenify -o cleaned_project/ project/

# Recursively target via glob patterns
tokenify "src/**/*.py"

# Compress output using lzma into cleaned_project
tokenify -o cleaned_project -z -a lzma project/
```

### Options

| Flag                         | Description                                               |
|------------------------------|-----------------------------------------------------------|
| `-i`, `--in-place`           | Overwrite original files                                  |
| `-o`, `--output-dir DIR`     | Directory to write processed files                        |
| `-z`, `--compress`           | Compress output (appends `.gz`, `.bz2`, or `.xz`)         |
| `-a`, `--algorithm ALG`      | Compression algorithm: `gzip`, `bz2`, `lzma` (default: gzip) |

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/YourFeature`.
3. Commit your changes: `git commit -m "Add some feature"`.
4. Push to the branch: `git push origin feature/YourFeature`.
5. Open a Pull Request.

Please adhere to the existing code style and include unit tests for new features.

## 📄 License

This project is licensed under the **MIT License**.