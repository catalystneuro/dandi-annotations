import yaml
from pathlib import Path
from dandiannotations.models.models import AnnotationContributor, ExternalResource
from dandischema.models import RelationType, ResourceType

def main():
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    # Navigate to the external_resources directory relative to the script location
    external_resources_dir = script_dir.parent / 'external_resources'
    
    submitted_yaml_path = external_resources_dir / '20250730_102427_submission.yaml'
    with open(submitted_yaml_path, 'r') as f:
        metadata = yaml.safe_load(f)

    metadata["annotation_contributor"] = AnnotationContributor(**metadata['annotation_contributor'])
    metadata["relation"] = RelationType(metadata['relation'])
    metadata["resourceType"] = ResourceType(metadata['resourceType'])
    submitted_resource = ExternalResource(**metadata)

    approved_yaml_path = external_resources_dir / '20250729_152555_submission.yaml'
    with open(approved_yaml_path, 'r') as f:
        metadata = yaml.safe_load(f)
    metadata["annotation_contributor"] = AnnotationContributor(**metadata['annotation_contributor'])
    metadata["approval_contributor"] = AnnotationContributor(**metadata['approval_contributor'])
    metadata["relation"] = RelationType(metadata['relation'])
    metadata["resourceType"] = ResourceType(metadata['resourceType'])
    approved_resource = ExternalResource(**metadata)

    print("Created submitted resource:")
    print(f"Name: {submitted_resource.name}")
    print(f"Identifier: {submitted_resource.identifier}")
    print(f"Relation: {submitted_resource.relation}")
    print(f"Annotation Contributor: {submitted_resource.annotation_contributor}")
    print(f"Annotation Date: {submitted_resource.annotation_date}")
    print(f"Schema Key: {submitted_resource.schemaKey}")

    print("\nCreated approved resource:")
    print(f"Name: {approved_resource.name}")
    print(f"Identifier: {approved_resource.identifier}")
    print(f"Relation: {approved_resource.relation}")
    print(f"Annotation Contributor: {approved_resource.annotation_contributor}")
    print(f"Annotation Date: {approved_resource.annotation_date}")
    print(f"Approval Contributor: {approved_resource.approval_contributor}")
    print(f"Approval Date: {approved_resource.approval_date}")
    print(f"Schema Key: {approved_resource.schemaKey}")

if __name__ == '__main__':
    main()
