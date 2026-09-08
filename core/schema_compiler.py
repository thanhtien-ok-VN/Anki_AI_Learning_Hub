"""Schema Compiler: Compiles Pydantic Models to Google Gemini OpenAPI JSON Schemas.

Enforces a Single Source of Truth by deriving Gemini API schema definitions directly
from Pydantic models, eliminating manual maintenance of duplicate raw dict schemas.
"""
from typing import Any, Dict, Optional

TYPE_MAP = {
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
    "array": "ARRAY",
    "object": "OBJECT",
}

_SCHEMA_CACHE: Dict[Any, Dict[str, Any]] = {}


def compile_model_to_gemini_schema(model: Any) -> Dict[str, Any]:
    """Compiles a Pydantic model class to Gemini API JSON schema format."""
    if model is None:
        return {}

    if model in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[model]

    # Support Pydantic V2 (model_json_schema) and V1 (schema)
    if hasattr(model, "model_json_schema"):
        raw_schema = model.model_json_schema()
    elif hasattr(model, "schema"):
        raw_schema = model.schema()
    elif isinstance(model, dict):
        return model
    else:
        return {}

    defs = raw_schema.get("$defs", raw_schema.get("definitions", {}))

    def resolve_ref(ref_str: str) -> dict:
        def_name = ref_str.split("/")[-1]
        return defs.get(def_name, {})

    def convert_prop(prop_schema: dict) -> dict:
        if "$ref" in prop_schema:
            prop_schema = resolve_ref(prop_schema["$ref"])

        # Handle Optional / Union types (anyOf)
        if "anyOf" in prop_schema:
            for item in prop_schema["anyOf"]:
                if item.get("type") != "null":
                    return convert_prop(item)

        p_type = prop_schema.get("type", "string")

        if p_type == "array":
            items_schema = prop_schema.get("items", {})
            return {
                "type": "ARRAY",
                "items": convert_prop(items_schema)
            }
        elif p_type == "object" or "properties" in prop_schema:
            props = prop_schema.get("properties", {})
            req = prop_schema.get("required", [])
            converted_props = {k: convert_prop(v) for k, v in props.items()}
            res: Dict[str, Any] = {
                "type": "OBJECT",
                "properties": converted_props
            }
            if req:
                res["required"] = req
            return res
        else:
            return {"type": TYPE_MAP.get(p_type, "STRING")}

    props = raw_schema.get("properties", {})
    req = raw_schema.get("required", [])
    converted_props = {k: convert_prop(v) for k, v in props.items()}

    res: Dict[str, Any] = {
        "type": "OBJECT",
        "properties": converted_props
    }
    if req:
        res["required"] = req

    _SCHEMA_CACHE[model] = res
    return res
