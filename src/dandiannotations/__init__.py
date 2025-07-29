"""
DANDI External Resources Annotations Package

This package provides tools for creating and managing external resource annotations 
for DANDI datasets, including Pydantic models and utilities.
"""

from .models.models import AnnotationContributor, ExternalResource

__version__ = "0.1.0"
__all__ = ["AnnotationContributor", "ExternalResource"]
