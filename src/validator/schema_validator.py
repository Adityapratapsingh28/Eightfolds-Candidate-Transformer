import jsonschema
from typing import Any, Dict
from src.models.config import ProjectionConfig
from src.utils.exceptions import ValidationError

class SchemaValidator:
    """
    Validates output JSON profiles against target schemas.
    """
    def validate(self, output_json: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validates output_json against a raw JSON schema dict.
        """
        try:
            jsonschema.validate(instance=output_json, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(f"Schema validation failed: {e.message}") from e

    def validate_projected_output(self, output_json: Dict[str, Any], config: ProjectionConfig) -> bool:
        """
        Dynamically generates a JSON Schema from a ProjectionConfig and validates output_json.
        """
        # Build JSON Schema properties
        properties = {}
        required = []

        for field in config.fields:
            field_type = field.type
            # Map type to JSON Schema type definition
            if field_type == "string":
                schema_type = {"type": "string"}
            elif field_type == "string[]":
                schema_type = {"type": "array", "items": {"type": "string"}}
            elif field_type == "number":
                schema_type = {"type": "number"}
            elif field_type == "object":
                schema_type = {"type": "object"}
            elif field_type == "object[]":
                schema_type = {"type": "array", "items": {"type": "object"}}
            else:
                schema_type = {}

            # Handle Pydantic config on_missing policy.
            # If on_missing is "null", the type can also be null
            if config.on_missing == "null":
                if "type" in schema_type:
                    # Make it nullable: e.g. ["string", "null"]
                    t = schema_type["type"]
                    if isinstance(t, str):
                        schema_type["type"] = [t, "null"]

            properties[field.path] = schema_type

            if field.required:
                required.append(field.path)

        # Append optional toggles to properties
        if config.include_confidence:
            properties["overall_confidence"] = {"type": "number"}
        if config.include_provenance:
            properties["provenance"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "source": {"type": "string"},
                        "method": {"type": "string"}
                    },
                    "required": ["field", "source", "method"]
                }
            }

        # Construct final JSON Schema
        generated_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False  # Only allow projected keys, confidence, and provenance
        }

        return self.validate(output_json, generated_schema)

