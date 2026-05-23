"""Action handlers for the automation rule engine.

Each action type is implemented as a handler function.
"""
from typing import Any


async def handle_notify(action: dict, context: dict) -> dict:
    channel = action.get("channel", "unknown")
    template = action.get("template", "default")
    # TODO: Implement actual notification dispatch
    return {
        "channel": channel,
        "template": template,
        "status": "queued",
    }


async def handle_log(action: dict, context: dict) -> dict:
    # Simple logging action — useful for debugging rules
    return {
        "message": f"Rule evaluated at {context.get('_evaluated_at', 'unknown')}",
        "context_snapshot": {k: v for k, v in context.items() if not k.startswith("_")},
    }


ACTION_HANDLERS = {
    "notify": handle_notify,
    "log": handle_log,
}


def get_handler(action_type: str):
    handler = ACTION_HANDLERS.get(action_type)
    if not handler:
        raise ValueError(f"No handler registered for action type: {action_type}")
    return handler
