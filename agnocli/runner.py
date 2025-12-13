from __future__ import annotations

import asyncio
from typing import Any, Dict

from .workflows import Workflow


async def _maybe_await(result):
    if asyncio.iscoroutine(result):
        return await result
    return result


async def run_workflow_async(wf: Workflow, params: Dict[str, Any]) -> Any:
    fn = wf.func
    if asyncio.iscoroutinefunction(fn):
        return await fn(**params)
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(**params))


def run_workflow(wf: Workflow, params: Dict[str, Any]) -> Any:
    try:
        return asyncio.run(run_workflow_async(wf, params))
    except RuntimeError:
        # Already in an event loop (e.g., notebook); fallback
        return asyncio.get_event_loop().create_task(run_workflow_async(wf, params))
