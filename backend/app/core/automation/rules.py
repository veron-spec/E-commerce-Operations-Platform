"""Pre-built rule templates for common automation scenarios.

These can be used as starting points for creating automation rules.
"""

LOW_STOCK_ALERT = {
    "name": "Low Stock Alert",
    "trigger_type": "scheduled",
    "conditions": {
        "field": "inventory_quantity",
        "operator": "lt",
        "value": 10,
    },
    "actions": [
        {
            "type": "notify",
            "channel": "email",
            "template": "low_stock_alert",
        }
    ],
}

HIGH_SALES_ALERT = {
    "name": "High Sales Spike Alert",
    "trigger_type": "scheduled",
    "conditions": {
        "field": "daily_revenue",
        "operator": "gt",
        "value": 10000,
    },
    "actions": [
        {
            "type": "notify",
            "channel": "email",
            "template": "sales_spike_alert",
        }
    ],
}
