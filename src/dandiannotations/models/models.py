from dandischema.models import Resource, DandiBaseModel, Identifier
from dandischema.models import EmailStr, AnyHttpUrl
from pydantic import Field
from typing import Literal, Optional
from datetime import datetime

class AnnotationContributor(DandiBaseModel):
    identifier: Optional[Identifier] = Field(
        None,
        title="A common identifier",
        description="Use a common identifier such as ORCID (orcid.org) for "
        "people or ROR (ror.org) for institutions.",
        json_schema_extra={"nskey": "schema"},
    )
    name: Optional[str] = Field(None, json_schema_extra={"nskey": "schema"})
    email: Optional[EmailStr] = Field(None, json_schema_extra={"nskey": "schema"})
    url: Optional[AnyHttpUrl] = Field(None, json_schema_extra={"nskey": "schema"})
    
    schemaKey: Literal["AnnotationContributor"] = Field(
        "AnnotationContributor", validate_default=True, json_schema_extra={"readOnly": True}
    )

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
    endorsement_contributor: Optional[AnnotationContributor] = Field(
        default=None,
        title="Endorsement Contributor",
        description="Person or organization who endorsed this resource"
    )
    endorsement_date: Optional[datetime] = Field(
        default=None,
        title="Endorsement Date",
        description="When this resource was endorsed by a moderator"
    )
    
    schemaKey: Literal["ExternalResource"] = Field(
        "ExternalResource", validate_default=True, json_schema_extra={"readOnly": True}
    )
