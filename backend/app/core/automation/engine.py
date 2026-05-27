"""Automation Rule Engine — evaluates conditions and executes actions.

Rule structure (JSON stored in automation_rules.conditions / .actions):

conditions:
  {
    "field": "inventory_quantity",
    "operator": "lt",
    "value": 10
  }

actions:
  {
    "type": "notify",
    "channel": "email",
    "recipient": "admin@example.com",
    "template": "low_stock_alert"
  }
"""
from typing import Any

from app.models.automation_rule import AutomationRule


class RuleEngine:
    """Evaluates automation rules against current data state."""

    OPERATORS = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
        "in": lambda a, b: a in b,
        "contains": lambda a, b: b in a,
    }

    async def evaluate_rule(self, rule: AutomationRule, context: dict[str, Any]) -> bool:
        """Evaluate whether a rule's conditions are met in the given context."""
        if not rule.is_enabled:
            return False

        conditions = rule.conditions or {}
        field = conditions.get("field")
        operator = conditions.get("operator", "eq")
        value = conditions.get("value")

        if not field or operator not in self.OPERATORS:
            return False

        actual_value = context.get(field)
        op_func = self.OPERATORS[operator]

        try:
            return op_func(actual_value, value)
        except (TypeError, ValueError):
            return False

    async def execute_actions(self, rule: AutomationRule, context: dict[str, Any]) -> list[dict]:
        """Execute the actions defined in a rule.

        Returns a list of action results.
        """
        actions = rule.actions or []
        if isinstance(actions, dict):
            actions = [actions]

        results = []
        for action in actions:
            action_type = action.get("type", "unknown")
            try:
                result = await self._dispatch_action(action_type, action, context)
                results.append({"type": action_type, "status": "executed", "result": result})
            except Exception as e:
                results.append({"type": action_type, "status": "failed", "error": str(e)})

        return results

    async def _dispatch_action(self, action_type: str, action: dict, context: dict) -> Any:
        """Dispatch to the appropriate action handler.

        TODO: Implement actual action handlers:
        - notify: Send notification (email, SMS, Slack)
        - update_product: Update product price/status via adapter
        - create_discount: Create a discount/coupon
        - sync_inventory: Trigger inventory sync
        """
        if action_type == "notify":
            return {"message": f"Notification queued: {action.get('channel', 'unknown')}"}
        elif action_type == "log":
            return {"message": f"Logged: {context}"}
        else:
            raise ValueError(f"Unknown action type: {action_type}")
