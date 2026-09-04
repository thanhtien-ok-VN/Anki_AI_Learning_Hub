"""Compatibility adapter for results saved before locale-neutral AI fields."""

_LEGACY_FIELDS = {"meaning_vi": "meaning", "reason_vi": "reason", "explanation_vi": "explanation"}

def normalize_language_fields(value):
    if isinstance(value, list):
        return [normalize_language_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    normalized = {key: normalize_language_fields(item) for key, item in value.items()}
    for legacy, neutral in _LEGACY_FIELDS.items():
        if not normalized.get(neutral) and normalized.get(legacy):
            normalized[neutral] = normalized[legacy]
    return normalized
