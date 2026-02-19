from typing import List, Dict, Any, Type
from pydantic import BaseModel, ValidationError

def identify_missing_slots(model_class: Type[BaseModel], data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identifies which required fields are missing from the data for a given Pydantic model.
    Returns a list of dicts with field name and description.
    """
    missing = []
    schema = model_class.model_json_schema()
    required = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required:
        if field not in data or data[field] is None:
            missing.append({
                "name": field,
                "description": properties.get(field, {}).get('description', ''),
                "type": properties.get(field, {}).get('type', 'any')
            })

    return missing

def validate_physics(model_instance: BaseModel) -> List[str]:
    """
    Performs additional physical consistency checks that might not be caught by simple field limits.
    """
    errors = []
    # Example: Check if Nc/Nv are physically reasonable for the given temperature
    # (Simplified for now)
    return errors
