from dandischema.models import Resource, DandiBaseModel, Identifier
from dandischema.models import EmailStr, AnyHttpUrl
from pydantic import Field, field_validator, ValidationError
from typing import Literal, Optional
from datetime import datetime
import re

class AnnotationContributor(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None,
        title="A common identifier",
        description="Use a common identifier such as ORCID (orcid.org).",
        json_schema_extra={"nskey": "schema"},
    )
    name: str = Field(title="Name", json_schema_extra={"nskey": "schema"})
    email: EmailStr = Field(title="Email", json_schema_extra={"nskey": "schema"})
    url: Optional[AnyHttpUrl] = Field(None, json_schema_extra={"nskey": "schema"})
    
    schemaKey: Literal["AnnotationContributor"] = Field(
        "AnnotationContributor", validate_default=True, json_schema_extra={"readOnly": True}
    )

    @field_validator('identifier')
    @classmethod
    def validate_orcid(cls, v):
        """Validate ORCID format to match frontend validation"""
        if v is None:
            return v
        
        # Convert to string for validation
        identifier_str = str(v)
        
        # ORCID pattern matching frontend: https://orcid.org/XXXX-XXXX-XXXX-XXXX
        orcid_pattern = r'^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
        
        # Check if it looks like an ORCID (contains orcid.org)
        if 'orcid.org' in identifier_str.lower():
            if re.match(orcid_pattern, identifier_str):
                return identifier_str
            else:
                raise ValueError('Please enter a valid ORCID URL (e.g., https://orcid.org/0000-0000-0000-0000)') 
        return v       

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format to match frontend validation"""
        if v is None:
            return v
        
        url_str = str(v)
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        
        if not re.match(url_pattern, url_str):
            raise ValueError('Please enter a valid URL starting with http:// or https://')
        
        return v

class ExternalResource(Resource):
    dandiset_id: str = Field(
        title="DANDI Set ID",
        description="The DANDI set identifier this resource is associated with (e.g., '000001')"
    )
    annotation_contributor: AnnotationContributor = Field(
        title="Annotation Contributor",
        description="Person or organization who annotated this resource"
    )
    annotation_date: datetime = Field(
        title="Annotation Date", 
        description="When this resource annotation was created"
    )
    approval_contributor: Optional[AnnotationContributor] = Field(
        default=None,
        title="Approval Contributor",
        description="Person or organization who approved this resource"
    )
    approval_date: Optional[datetime] = Field(
        default=None,
        title="Approval Date",
        description="When this resource was approved by a moderator"
    )
    
    schemaKey: Literal["ExternalResource"] = Field(
        "ExternalResource", validate_default=True, json_schema_extra={"readOnly": True}
    )

    @field_validator('dandiset_id')
    @classmethod
    def validate_dandiset_id(cls, v):
        """Validate Dandiset ID"""
        dandiset_pattern = r'^([0-9]{6})$'
        if re.match(dandiset_pattern, v):
            return v
        else:
            raise ValueError('Enter 6-digit DANDI set ID (e.g., 000001)')
