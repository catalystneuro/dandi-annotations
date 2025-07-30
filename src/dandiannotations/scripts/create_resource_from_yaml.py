import yaml
from dandiannotations.models.models import AnnotationContributor, ExternalResource
from dandischema.models import RelationType, ResourceType

def main():
    with open('src/dandiannotations/external_resources/20250730_102427_submission.yaml', 'r') as f:
        metadata = yaml.safe_load(f)

    metadata["annotation_contributor"] = AnnotationContributor(**metadata['annotation_contributor'])
    metadata["relation"] = RelationType(metadata['relation'])
    metadata["resourceType"] = ResourceType(metadata['resourceType'])
    submitted_resource = ExternalResource(**metadata)

    with open('src/dandiannotations/external_resources/20250729_152555_submission.yaml', 'r') as f:
        metadata = yaml.safe_load(f)
    metadata["annotation_contributor"] = AnnotationContributor(**metadata['annotation_contributor'])
    metadata["endorsement_contributor"] = AnnotationContributor(**metadata['endorsement_contributor'])
    metadata["relation"] = RelationType(metadata['relation'])
    metadata["resourceType"] = ResourceType(metadata['resourceType'])
    endorsed_resource = ExternalResource(**metadata)

    print("Created submitted resource:")
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
    print(f"Schema Key: {endorsed_resource.schemaKey}")

if __name__ == '__main__':
    main()
