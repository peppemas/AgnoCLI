### AgnoCLI — Multiplatform Terminal for Agno Workflows

AgnoCLI is a Python-based terminal application to discover and run workflows built with the `agno` framework. It supports:

- Listing and switching between workflows
- Running workflows with parameters
- Terminal-only interactive mode (no windows/tabs)
- ANSI colors and Markdown rendering (including tables)
- Config via `agnocli.yaml`
- Rotating file logs
- Packaging into single-file executables for Windows, macOS, and Linux

#### Requirements
- Python 3.9+
- Install dependencies:
```
pip install -r requirements.txt
```

#### Configure
Create an `agnocli.yaml` in your project (or place it in the OS config path). Example:
```
workflows_module: sample_workflows
log_dir: ./logs
default_workflow: hello
markdown:
  render: true
ansi:
  force: false
```

AgnoCLI searches for `agnocli.yaml` in:
- Current working directory
- OS config dir: `~/.config/agnocli/agnocli.yaml` (Linux), `~/Library/Application Support/agnocli/agnocli.yaml` (macOS), `%APPDATA%\agnocli\agnocli.yaml` (Windows)

#### Define Workflows
Workflows are registered via a decorator:
```
from agnocli.workflows import register_workflow

@register_workflow(name="hello", description="Hello example", render_markdown=True)
def hello(name: str = "world"):
    return f"# Hello, {name}!\n\nThis is **Markdown** with a table:\n\n| A | B |\n|---|---|\n| 1 | 2 |"
```

Point `workflows_module` to the Python module where these functions live.

You can set `render_markdown=False` per workflow to force plain output, or leave it unset to use config/CLI defaults.

#### CLI Usage
```
python -m agnocli list
python -m agnocli switch hello
python -m agnocli current
python -m agnocli run hello --arg name=Agno
python -m agnocli run --markdown/--plain
python -m agnocli tui
```

Options that override config:
- `--module <module.path>`
- `--config <path>`
- `--render/--no-render`
- `--force-ansi/--no-force-ansi`

#### Logs
Logs are written to a rotating file (default 10 MB, 5 backups) under `log_dir`.

#### Build Single-File Executables (PyInstaller)
Install PyInstaller:
```
pip install pyinstaller
```

Build (Windows/macOS/Linux):
```
pyinstaller --onefile -n agnocli agnocli/__main__.py
```
Artifacts will be under `dist/` as `agnocli` (or `agnocli.exe` on Windows).

Example cross-platform CI can be added later (GitHub Actions matrix for `windows-latest`, `macos-latest`, `ubuntu-latest`).
