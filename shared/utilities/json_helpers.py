"""
JSON Helpers Utility
====================

Provides JSON serialization and deserialization utilities.
"""

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


def to_json(obj: Any, indent: int = 2) -> str:
    """
    Serialize an object to JSON string.
    
    Handles dataclasses, enums, and standard types.
    
    Args:
        obj: Object to serialize
        indent: JSON indentation level
        
    Returns:
        JSON string
    """
    if is_dataclass(obj):
        obj = asdict(obj)
    
    def _default_serializer(o: Any) -> Any:
        if hasattr(o, "value"):  # Enum
            return o.value
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)
    
    return json.dumps(obj, default=_default_serializer, indent=indent)


def from_json(json_str: str, cls: Type[T]) -> T:
    """
    Deserialize a JSON string to an object.
    
    Args:
        json_str: JSON string to deserialize
        cls: Target class type
        
    Returns:
        Deserialized object
        
    Note:
        This is a basic implementation. Complex deserialization
        may require custom logic per class.
    """
    data = json.loads(json_str)
    
    if is_dataclass(cls):
        return cls(**data)
    
    return data


def to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert an object to a dictionary.
    
    Args:
        obj: Object to convert
        
    Returns:
        Dictionary representation
    """
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    if isinstance(obj, dict):
        return obj
    return {"value": obj}


def from_dict(data: Dict[str, Any], cls: Type[T]) -> T:
    """
    Create an object from a dictionary.
    
    Args:
        data: Dictionary data
        cls: Target class type
        
    Returns:
        Created object
    """
    if is_dataclass(cls):
        return cls(**data)
    return data


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
