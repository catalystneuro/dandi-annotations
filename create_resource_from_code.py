from src.dandiannotations.models import AnnotationContributor, ExternalResource
from dandischema.models import RelationType
from datetime import datetime

def main():
   resource = ExternalResource(
       name="TestResource",
       identifier="123",
       relation=RelationType.IsCitedBy,
       annotation_contributor=AnnotationContributor(
           name="Jane Smith",
           email="jane.smith@example.com",
           url="https://example.com/jane-smith"
       ),
       annotation_date=datetime.strptime("2024-07-25T10:30:00", "%Y-%m-%dT%H:%M:%S"),
   )
   
   print("Created annotated resource:")
   print(f"Name: {resource.name}")
   print(f"Identifier: {resource.identifier}")
   print(f"Relation: {resource.relation}")
   print(f"Annotation Contributor: {resource.annotation_contributor}")
   print(f"Annotation Date: {resource.annotation_date}")
   print(f"Schema Key: {resource.schemaKey}")
   
   print("\nAs JSON:")
   print(resource.model_dump_json(indent=2))

if __name__ == '__main__':
   main()