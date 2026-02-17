from __future__ import annotations

from typing import Dict, List, Optional
import shlex
import inspect

import click
import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import load_config
from .logging_setup import setup_logging
from .markdown import get_console, render_markdown, render_plain
from .runner import run_workflow
from .state import get_current_workflow, set_current_workflow
from .workflows import discover_from_module, get_workflow, list_workflows, Workflow

app = typer.Typer(add_completion=False, help="Agno CLI to discover and run workflows.")


def _parse_args(kvs: List[str]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for item in kvs:
        if "=" not in item:
            raise typer.BadParameter(f"Invalid arg '{item}'. Use key=value format.")
        k, v = item.split("=", 1)
        parsed[k] = v
    return parsed


def _ensure_discovery(cfg_module: Optional[str]):
    if not cfg_module:
        raise typer.Exit("workflows_module is not configured in agnocli.yaml and not provided via --module")
    discover_from_module(cfg_module)

def _should_render_markdown(
    markdown_option: Optional[bool],
    wf: Workflow,
    cfg_render_default: bool,
) -> bool:
    if markdown_option is not None:
        return markdown_option
    if wf.render_markdown is not None:
        return wf.render_markdown
    return cfg_render_default


@app.callback()
def main(
    ctx: typer.Context,
    module: Optional[str] = typer.Option(None, "--module", help="Python module path to workflows (overrides config)"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to agnocli.yaml"),
    render: Optional[bool] = typer.Option(None, "--render/--no-render", help="Render markdown output"),
    force_ansi: Optional[bool] = typer.Option(None, "--force-ansi/--no-force-ansi", help="Force ANSI output"),
):
    cfg = load_config(config)
    if module:
        cfg.workflows_module = module
    if render is not None:
        cfg.markdown.render = render
    if force_ansi is not None:
        cfg.ansi.force = force_ansi

    logger = setup_logging(cfg.log_dir)
    ctx.obj = {"cfg": cfg, "logger": logger}

@app.command()
def list():
    """List available workflows."""
    ctx = click.get_current_context()
    cfg = ctx.obj["cfg"]
    _ensure_discovery(cfg.workflows_module)

    console = get_console(cfg.ansi.force)
    table = Table(title="Available Workflows")
    table.add_column("Name", style="bold cyan")
    table.add_column("Description")
    for name, wf in list_workflows().items():
        table.add_row(name, wf.description or "")
    console.print(table)

@app.command()
def current():
    """Show current active workflow (from state)."""
    ctx = click.get_current_context()
    cfg = ctx.obj["cfg"]
    _ensure_discovery(cfg.workflows_module)
    cur = get_current_workflow() or cfg.default_workflow
    console = get_console(cfg.ansi.force)
    if cur:
        console.print(Panel.fit(Text(f"Current workflow: {cur}", style="green")))
    else:
        console.print(Panel.fit(Text("No workflow set. Use 'agnocli switch <name>'", style="yellow")))


@app.command()
def switch(name: str):
    """Set current active workflow."""
    ctx = click.get_current_context()
    cfg = ctx.obj["cfg"]
    _ensure_discovery(cfg.workflows_module)
    if name not in list_workflows():
        raise typer.Exit(f"Workflow '{name}' not found")
    set_current_workflow(name)
    console = get_console(cfg.ansi.force)
    console.print(Panel.fit(Text(f"Switched to workflow: {name}", style="green")))


@app.command()
def run(
    name: Optional[str] = typer.Argument(None, help="Workflow name; if omitted uses current/default"),
    arg: List[str] = typer.Option([], "--arg", help="Pass parameter as key=value. Repeatable."),
    markdown: Optional[bool] = typer.Option(None, "--markdown/--plain", help="Render output as markdown or plain"),
):
    """Run a workflow with optional parameters."""
    ctx = click.get_current_context()
    cfg = ctx.obj["cfg"]
    _ensure_discovery(cfg.workflows_module)

    selected = name or get_current_workflow() or cfg.default_workflow
    if not selected:
        raise typer.Exit("No workflow selected. Provide a name or set current/default.")

    wf = get_workflow(selected)
    if not wf:
        raise typer.Exit(f"Workflow '{selected}' not found")

    params = _parse_args(arg)
    result = run_workflow(wf, params)

    console = get_console(cfg.ansi.force)
    render_md = _should_render_markdown(markdown, wf, cfg.markdown.render)
    if isinstance(result, str) and render_md:
        render_markdown(console, result)
    else:
        render_plain(console, str(result))


@app.command()
def tui():
    """Interactive terminal mode (no windows/tabs)."""
    ctx = click.get_current_context()
    cfg = ctx.obj["cfg"]
    _ensure_discovery(cfg.workflows_module)

    console = get_console(cfg.ansi.force)

    def _list(wfs: List[Workflow]) -> List[Workflow]:
        return sorted(wfs, key=lambda wf: wf.name.lower())

    def _prompt_for_params(wf: Workflow, provided: Dict[str, str]) -> Dict[str, object]:
        try:
            sig = inspect.signature(wf.func)
        except (ValueError, TypeError):
            return provided
        params: Dict[str, object] = dict(provided)
        for name, param in sig.parameters.items():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if name in params:
                continue
            default = param.default
            has_default = default is not inspect._empty
            while True:
                if has_default:
                    prompt = f"{name} [default={default}]: "
                else:
                    prompt = f"{name}: "
                try:
                    value = input(prompt).strip()
                except (EOFError, KeyboardInterrupt):
                    console.print("Exiting.")
                    raise typer.Exit()
                if value:
                    params[name] = value
                    break
                if has_default:
                    params[name] = default
                    break
                console.print(Text(f"'{name}' is required", style="red"))
        return params

    def _pause():
        """Wait for the user to press Enter before returning to the menu."""
        console.print()
        console.rule(style="dim")
        try:
            input("Press Enter to return to menu...")
        except (EOFError, KeyboardInterrupt):
            pass

    def draw_menu():
        console.clear()
        console.rule("AgnoCLI")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        wfs = _list(list_workflows().values())
        for i, wf in enumerate(wfs, start=1):
            table.add_row(str(i), wf.name, wf.description or "")
        console.print(table)
        console.print(
            "Commands: [number]=run, s [number]=switch, r [name]=run, <name> [key=value ...]=run with args, q=quit"
        )
        return wfs

    while True:
        wfs = draw_menu()
        try:
            cmd = input(": ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("Exiting.")
            break
        if not cmd:
            continue
        if cmd.lower() in {"q", "quit", "exit"}:
            break
        # Unified command parsing: support both ": image ..." and "image ..."
        # If the line starts with a colon, strip it, then fall through to the same parser.
        if cmd.startswith(":"):
            cmd = cmd[1:].lstrip()
        # Try to interpret the command as: <workflow_name> [key=value ...]
        try:
            parts = shlex.split(cmd)
        except ValueError as e:
            # If it wasn't a colon form and also not parsable, we'll handle other commands below
            parts = []
        if parts:
            name = parts[0]
            wf = get_workflow(name)
            if wf:
                kv_items = [p for p in parts[1:] if "=" in p]
                try:
                    params = _parse_args(kv_items)
                except typer.BadParameter as e:
                    console.print(Text(str(e), style="red"))
                    continue
                # Filter unknown params based on workflow signature to avoid TypeError
                try:
                    sig = inspect.signature(wf.func)
                    valid_keys = set(sig.parameters.keys())
                    filtered_params = {k: v for k, v in params.items() if k in valid_keys}
                    unknown = set(params.keys()) - valid_keys
                    if unknown:
                        console.print(Text(f"Ignoring unknown params: {', '.join(sorted(unknown))}", style="yellow"))
                except (ValueError, TypeError):
                    # If signature unavailable, pass as-is
                    filtered_params = params
                filtered_params = _prompt_for_params(wf, filtered_params)
                result = run_workflow(wf, filtered_params)
                render_md = _should_render_markdown(None, wf, cfg.markdown.render)
                if isinstance(result, str) and render_md:
                    render_markdown(console, result)
                else:
                    render_plain(console, str(result))
                _pause()
                continue
        if cmd[0].isdigit():
            try:
                idx = int(cmd) - 1
                wf = wfs[idx]
            except Exception:
                console.print(Text("Invalid selection", style="red"))
                continue
            params = _prompt_for_params(wf, {})
            result = run_workflow(wf, params)
            render_md = _should_render_markdown(None, wf, cfg.markdown.render)
            if isinstance(result, str) and render_md:
                render_markdown(console, result)
            else:
                render_plain(console, str(result))
            _pause()
            continue
        if cmd.startswith("s "):
            try:
                idx = int(cmd.split()[1]) - 1
                wf = wfs[idx]
                set_current_workflow(wf.name)
                console.print(Text(f"Switched to {wf.name}", style="green"))
            except Exception:
                console.print(Text("Invalid switch command", style="red"))
            continue
        if cmd.startswith("r "):
            name = cmd.split(maxsplit=1)[1]
            wf = get_workflow(name)
            if not wf:
                console.print(Text(f"Workflow '{name}' not found", style="red"))
                continue
            params = _prompt_for_params(wf, {})
            result = run_workflow(wf, params)
            render_md = _should_render_markdown(None, wf, cfg.markdown.render)
            if isinstance(result, str) and render_md:
                render_markdown(console, result)
            else:
                render_plain(console, str(result))
            _pause()
            continue
        console.print(Text("Unknown command", style="yellow"))


def run():
    app()
