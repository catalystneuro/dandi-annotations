from dandiannotations.models.models import AnnotationContributor, ExternalResource
from dandischema.models import RelationType, ResourceType
from datetime import datetime

def main():
   submitted_resource = ExternalResource(
       name="TestResource",
       identifier="123",
       dandiset_id="000001",
       relation=RelationType.IsCitedBy,
       resourceType=ResourceType.JournalArticle,
       annotation_contributor=AnnotationContributor(
           name="Jane Smith",
           email="jane.smith@example.com",
           url="https://example.com/jane-smith"
       ),
       annotation_date=datetime.strptime("2024-07-25T10:30:00", "%Y-%m-%dT%H:%M:%S"),
   )

   endorsed_resource = ExternalResource(
       name="EndorsedResource",
       identifier="456",
       dandiset_id="000001",
       relation=RelationType.IsCitedBy,
       resourceType=ResourceType.JournalArticle,
       annotation_contributor=AnnotationContributor(
           name="John Doe",
           email="john.doe@example.com",
           url="https://example.com/john-doe"
       ),
       annotation_date=datetime.strptime("2024-07-26T11:00:00", "%Y-%m-%dT%H:%M:%S"),
       endorsement_contributor=AnnotationContributor(
           name="Moderator",
           email="moderator@example.com",
           url="https://example.com/moderator"
       ),
       endorsement_date=datetime.strptime("2024-07-27T12:00:00", "%Y-%m-%dT%H:%M:%S"),
   )

   print("Created annotated resource:")
   print(f"Name: {submitted_resource.name}")
   print(f"Identifier: {submitted_resource.identifier}")
   print(f"Relation: {submitted_resource.relation}")
   print(f"Annotation Contributor: {submitted_resource.annotation_contributor}")
   print(f"Annotation Date: {submitted_resource.annotation_date}")
   print(f"Schema Key: {submitted_resource.schemaKey}")
   
   print("\nCreated endorsed resource:")
   print(f"Name: {endorsed_resource.name}")
   print(f"Identifier: {endorsed_resource.identifier}")
   print(f"Relation: {endorsed_resource.relation}")
   print(f"Annotation Contributor: {endorsed_resource.annotation_contributor}")
   print(f"Annotation Date: {endorsed_resource.annotation_date}")
   print(f"Endorsement Contributor: {endorsed_resource.endorsement_contributor}")
   print(f"Endorsement Date: {endorsed_resource.endorsement_date}")

if __name__ == '__main__':
   main()
