"""
Utility functions for extracting schema options from DANDI schema
"""

from dandischema.models import RelationType, ResourceType


def _format_enum_name(name: str) -> str:
    """Convert enum name to human-readable format"""
    # Convert CamelCase to Title Case with spaces
    # e.g., "IsCitedBy" -> "Is Cited By"
    import re
    # Insert space before uppercase letters that follow lowercase letters
    formatted = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    return formatted


def get_resource_relation_options():
    """Get valid options for resource relation field from DANDI schema"""
    options = []
    for relation_type in RelationType:
        value = relation_type.value  # e.g., "dcite:IsCitedBy"
        display_name = _format_enum_name(relation_type.name)  # e.g., "Is Cited By"
        options.append((value, display_name))
    return sorted(options, key=lambda x: x[1])  # Sort by display name


def get_resource_type_options():
    """Get valid options for resource type field from DANDI schema"""
    options = []
    for resource_type in ResourceType:
        value = resource_type.value  # e.g., "dcite:Software"
        display_name = _format_enum_name(resource_type.name)  # e.g., "Software"
        options.append((value, display_name))
    return sorted(options, key=lambda x: x[1])  # Sort by display name
