from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


_REGISTRY: Dict[str, "Workflow"] = {}


@dataclass
class Workflow:
    name: str
    description: str
    func: Callable[..., Any]
    render_markdown: Optional[bool] = None


def register_workflow(
    name: Optional[str] = None,
    description: str = "",
    render_markdown: Optional[bool] = None,
):
    def decorator(func: Callable[..., Any]):
        wf_name = name or func.__name__
        _REGISTRY[wf_name] = Workflow(
            name=wf_name,
            description=description,
            func=func,
            render_markdown=render_markdown,
        )
        return func

    return decorator


def discover_from_module(module_path: str) -> Dict[str, Workflow]:
    # Import triggers decorator registration if present in module
    importlib.invalidate_caches()
    module = importlib.import_module(module_path)

    # Also scan module for callables with a `__agnoworkflow__` attribute if needed later
    # For now, rely on explicit decorator registration into _REGISTRY.
    return dict(_REGISTRY)


def list_workflows() -> Dict[str, Workflow]:
    return dict(_REGISTRY)


def get_workflow(name: str) -> Optional[Workflow]:
    return _REGISTRY.get(name)
