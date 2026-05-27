"""Recursively translate string values in API JSON responses."""


def translate_data(data, _):
    """Recursively translate string values (used by the API middleware)."""
    if data is None or isinstance(data, (bool, int, float)):
        return data
    if isinstance(data, str):
        return _(data)
    if isinstance(data, list):
        return [translate_data(item, _) for item in data]
    if isinstance(data, dict):
        return {k: translate_data(v, _) for k, v in data.items()}
    return data
