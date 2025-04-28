# tokenify

> A CLI tool to strip unnecessary comments from Python files.

## 🔍 Overview

`tokenify` helps you clean up Python code by removing standalone and inline comments, preserving shebangs and encoding lines. It supports:

* Directories (recursive scan).

* Individual `.py` files.

* Shell glob patterns (e.g. `src/**/*.py`).

## 🚀 Features

* **Strip comments**: removes all `#` comments while keeping code structure intact.

* **Flexible output**: in-place modification, custom output directory, or STDOUT.

* **Cross-platform**: runs anywhere Python3.7+ is available.

## 🛠️ Requirements

* **Python** >= 3.7 (no external dependencies; all features use the standard library).

## 🏗️ Development Setup

Before installing `tokenify`, create and activate a virtual environment to isolate dependencies:

```
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

```
# Clone the repo
git clone [https://github.com/catalinmoiceanu/tokenify.git](https://github.com/catalinmoiceanu/tokenify.git)
cd tokenify

# Install as an editable package
pip install --user -e src

```

This will install a `tokenify` command in your `~/.local/bin` (or equivalent). Ensure that directory is on your `PATH`.

Alternatively, after publishing to PyPI:

```
pip install tokenify

```

## ⚙️ Usage

```
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

```

### Options

| Flag | Description |
 | ----- | ----- |
| `-i`, `--in-place` | Overwrite original files |
| `-o`, `--output-dir DIR` | Directory to write processed files |

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
