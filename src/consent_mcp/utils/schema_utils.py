"""Utilities for converting Pydantic models to MCP input schemas."""

from typing import Any

from pydantic import BaseModel


def pydantic_to_input_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Convert a Pydantic model to an MCP tool inputSchema.

    This function extracts the JSON schema from a Pydantic model and transforms
    it into a format compatible with MCP tool definitions. It handles:
    - Required vs optional fields
    - Field descriptions
    - Type mappings (string, integer, boolean, etc.)
    - Optional types (anyOf with null)
    - Enum constraints
    - $ref references to $defs
    - Nested object models
    - Arrays of objects

    Args:
        model: The Pydantic model class to convert.

    Returns:
        A JSON Schema compatible dict for MCP inputSchema with:
        - type: "object"
        - properties: dict of field definitions
        - required: list of required field names

    Example:
        >>> from pydantic import BaseModel, Field
        >>> class MyRequest(BaseModel):
        ...     name: str = Field(description="User name")
        ...     age: int = Field(description="User age")
        >>> schema = pydantic_to_input_schema(MyRequest)
        >>> schema["properties"]["name"]["description"]
        'User name'
    """
    # Get JSON schema from Pydantic
    schema = model.model_json_schema()

    # Get $defs for resolving references
    defs = schema.get("$defs", {})

    # Build the input schema
    input_schema = _build_object_schema(schema, defs)

    return input_schema


def _build_object_schema(schema: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """
    Build an object schema from a Pydantic schema.

    Args:
        schema: The object schema definition.
        defs: The $defs dictionary for resolving references.

    Returns:
        A cleaned object schema for MCP.
    """
    result: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": schema.get("required", []),
    }

    for prop_name, prop_info in schema.get("properties", {}).items():
        clean_prop = _process_property(prop_info, defs)
        result["properties"][prop_name] = clean_prop

    return result


def _process_property(prop_info: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """
    Process a single property definition.

    Args:
        prop_info: The property info from Pydantic schema.
        defs: The $defs dictionary for resolving references.

    Returns:
        A cleaned property definition for MCP.
    """
    # Store original description before resolving refs
    original_description = prop_info.get("description")

    # Resolve $ref if present
    if "$ref" in prop_info:
        ref_path = prop_info["$ref"].split("/")[-1]
        resolved = defs.get(ref_path, {})

        # Check if this is a nested object
        if resolved.get("type") == "object" or "properties" in resolved:
            # Recursively build the nested object schema
            nested_schema = _build_object_schema(resolved, defs)
            if original_description:
                nested_schema["description"] = original_description
            return nested_schema

        # Merge with original to preserve description
        prop_info = {**resolved, **{k: v for k, v in prop_info.items() if k != "$ref"}}

    # Handle allOf (common pattern for constrained types)
    if "allOf" in prop_info:
        merged = {}
        for item in prop_info["allOf"]:
            if "$ref" in item:
                ref_path = item["$ref"].split("/")[-1]
                resolved_def = defs.get(ref_path, {})

                # Check if this is a nested object
                if resolved_def.get("type") == "object" or "properties" in resolved_def:
                    nested_schema = _build_object_schema(resolved_def, defs)
                    if original_description:
                        nested_schema["description"] = original_description
                    return nested_schema

                merged.update(resolved_def)
            else:
                merged.update(item)
        # Preserve description from original
        if "description" in prop_info:
            merged["description"] = prop_info["description"]
        prop_info = merged

    # Handle anyOf (e.g., for Optional types)
    if "anyOf" in prop_info:
        clean_prop = _handle_any_of(prop_info, defs)
    else:
        clean_prop = _extract_clean_property(prop_info, defs)

    return clean_prop


def _handle_any_of(prop_info: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """
    Handle anyOf schemas (typically Optional types).

    Args:
        prop_info: Property with anyOf.
        defs: The $defs dictionary for resolving references.

    Returns:
        Cleaned property definition.
    """
    clean_prop: dict[str, Any] = {}

    # Take the first non-null type
    for option in prop_info["anyOf"]:
        if option.get("type") != "null":
            # Check if this option is a reference
            if "$ref" in option:
                ref_path = option["$ref"].split("/")[-1]
                resolved = defs.get(ref_path, {})

                # Check if this is a nested object
                if resolved.get("type") == "object" or "properties" in resolved:
                    clean_prop = _build_object_schema(resolved, defs)
                else:
                    clean_prop = _extract_clean_property(resolved, defs)
            else:
                clean_prop = _extract_clean_property(option, defs)
            break

    # Preserve description from original if available
    if "description" in prop_info:
        clean_prop["description"] = prop_info["description"]

    return clean_prop


def _extract_clean_property(prop_info: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract a clean property definition with only MCP-relevant fields.

    Args:
        prop_info: The raw property info.
        defs: The $defs dictionary for resolving references.

    Returns:
        Cleaned property with only relevant fields.
    """
    # Handle nested object type
    if prop_info.get("type") == "object" or "properties" in prop_info:
        return _build_object_schema(prop_info, defs)

    # Handle array type with items
    if prop_info.get("type") == "array" and "items" in prop_info:
        items_info = prop_info["items"]

        # Resolve $ref in items if present
        if "$ref" in items_info:
            ref_path = items_info["$ref"].split("/")[-1]
            resolved_items = defs.get(ref_path, {})

            # Check if array items are objects
            if resolved_items.get("type") == "object" or "properties" in resolved_items:
                clean_items = _build_object_schema(resolved_items, defs)
            else:
                clean_items = _extract_clean_property(resolved_items, defs)
        else:
            clean_items = _extract_clean_property(items_info, defs)

        result: dict[str, Any] = {
            "type": "array",
            "items": clean_items,
        }
        if "description" in prop_info:
            result["description"] = prop_info["description"]
        elif "title" in prop_info:
            result["description"] = prop_info["title"]
        return result

    # Fields that are valid in MCP/JSON Schema for primitive types
    allowed_fields = {
        "type",
        "description",
        "enum",
        "default",
        "format",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "pattern",
    }

    clean_prop = {k: v for k, v in prop_info.items() if k in allowed_fields}

    # Use title as fallback description if no description exists
    if "description" not in clean_prop and "title" in prop_info:
        clean_prop["description"] = prop_info["title"]

    return clean_prop
