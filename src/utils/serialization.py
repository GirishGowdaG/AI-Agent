"""Serialization utilities for data models."""

import json
from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


class Serializer:
    """Handles serialization and deserialization of data models."""

    def serialize(self, obj: Any) -> str:
        """Convert a dataclass instance to JSON string.
        
        Args:
            obj: A dataclass instance to serialize
            
        Returns:
            JSON string representation of the object
        """
        if not is_dataclass(obj):
            raise TypeError(f"Expected dataclass, got {type(obj)}")
        
        return json.dumps(self._to_dict(obj), indent=2)

    def _to_dict(self, obj: Any) -> Any:
        """Recursively convert dataclass to dict, handling special types."""
        if is_dataclass(obj) and not isinstance(obj, type):
            return {k: self._to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        return obj

    def deserialize(self, json_str: str, model_class: Type[T]) -> T:
        """Reconstruct a dataclass instance from JSON string.
        
        Args:
            json_str: JSON string to deserialize
            model_class: The dataclass type to reconstruct
            
        Returns:
            Instance of model_class populated with data from JSON
        """
        if not is_dataclass(model_class):
            raise TypeError(f"Expected dataclass type, got {model_class}")
        
        data = json.loads(json_str)
        return self._from_dict(data, model_class)

    def _from_dict(self, data: Dict[str, Any], model_class: Type[T]) -> T:
        """Recursively reconstruct dataclass from dict."""
        if not is_dataclass(model_class):
            return data
        
        field_types = {f.name: f.type for f in fields(model_class)}
        kwargs = {}
        
        for field_name, value in data.items():
            if field_name not in field_types:
                continue
                
            field_type = field_types[field_name]
            kwargs[field_name] = self._convert_value(value, field_type)
        
        return model_class(**kwargs)

    def _convert_value(self, value: Any, field_type: Any) -> Any:
        """Convert a value to the appropriate type."""
        if value is None:
            return None
            
        # Handle string type annotations
        type_str = str(field_type)
        
        # Handle datetime
        if field_type == datetime or "datetime" in type_str:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
        
        # Handle List types
        if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
            item_type = field_type.__args__[0] if field_type.__args__ else str
            if is_dataclass(item_type):
                return [self._from_dict(item, item_type) for item in value]
            return value
        
        # Handle nested dataclasses
        if is_dataclass(field_type) and isinstance(value, dict):
            return self._from_dict(value, field_type)
        
        return value

    def validate_schema(self, json_str: str, model_class: Type) -> bool:
        """Validate that JSON conforms to the expected schema.
        
        Args:
            json_str: JSON string to validate
            model_class: The dataclass type to validate against
            
        Returns:
            True if valid, False otherwise
        """
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return False
            
            # Check required fields exist
            required_fields = {
                f.name for f in fields(model_class) 
                if f.default is f.default_factory  # No default value
            }
            
            # Check schema_version is present
            if "schema_version" not in data:
                return False
            
            return True
        except (json.JSONDecodeError, TypeError):
            return False
